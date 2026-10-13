"""ジブリ漢字クイズ「読めたら真のジブリファン」(YouTube ショート / TikTok 向け)

問題ごとに: 漢字を大きく表示 → 3・2・1 のカウントダウン → 「ピンポン」で読みと場面写真を表示。
背景は答えの作品の写真を強くぼかしたもの (ヒント)。答えを出す瞬間に、くっきりした写真が現れる。
使い方: python3 quiz-video/make.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import io
import json
import math
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "output"
SFX_DIR = ROOT / "chihiro-video" / "sfx"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = ROOT / "ghibli-video" / "fonts" / "NotoSansJP.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS, SR = 1080, 1920, 30, 44100
ENGINE = "http://localhost:50021"
SPEAKER = 2          # 四国めたん ノーマル
SPEED = 1.25
COUNT = 3            # カウントダウンの秒数
SFX_DB = -12
SAFE_RIGHT = int(W * 0.85)

RED = (225, 45, 45)
YELLOW = (255, 214, 0)

# 読みは Wikipedia (作品記事のふりがな) と作中のセリフで確認したもの
TITLE = dict(imgs=["nausicaa/009", "mononoke/024", "chihiro/011"],
             telop=["読めたら真の", "ジブリファン", "漢字クイズ"],
             voice="読めたら真のジブリファン！ジブリ漢字クイズ！")
QUESTIONS = [
    dict(kanji="油屋", yomi="あぶらや", stars=1, work="千と千尋の神隠し", img="chihiro/011"),
    dict(kanji="腐海", yomi="ふかい", stars=2, work="風の谷のナウシカ", img="nausicaa/002"),
    dict(kanji="王蟲", yomi="オーム", stars=3, work="風の谷のナウシカ", img="nausicaa/009"),
    dict(kanji="乙事主", yomi="おっことぬし", stars=4, work="もののけ姫", img="mononoke/037"),
    dict(kanji="猩々", yomi="しょうじょう", stars=5, work="もののけ姫", img="mononoke/026"),
]
ENDING = dict(img="mononoke/024", telop=["何問読めた？", "コメントで教えてね💬"],
              voice="何問読めた？コメントで教えてね！")


# ---- ナレーション -------------------------------------------------------------
def post(path, params, body=b""):
    req = urllib.request.Request(f"{ENGINE}{path}?{urllib.parse.urlencode(params)}", data=body,
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def synth(text):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            if m.get("consonant") and m["consonant_length"] < 0.045:
                m["consonant_length"] = 0.045
    q.update(speedScale=SPEED, pauseLengthScale=0.5, prePhonemeLength=0.0, postPhonemeLength=0.05,
             outputSamplingRate=SR, outputStereo=False)
    with wave.open(io.BytesIO(post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode()))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return (a[idx[0]: idx[-1] + 1] if len(idx) else a), q["kana"]


def build_timeline():
    """区間を作る。各区間: kind, start, end と、音声 (voices: [(秒, 波形)]) と効果音 (sfx: [(秒, 名前)])"""
    segs, t = [], 0.0
    a, kana = synth(TITLE["voice"])
    segs.append(dict(kind="title", start=0.0, end=round((0.15 + len(a) / SR + 0.5) * FPS) / FPS,
                     voices=[(0.15, a)], sfx=[(0.0, "question1.mp3")], kana=[kana]))
    t = segs[-1]["end"]
    for n, q in enumerate(QUESTIONS, 1):
        qa, k1 = synth(f"第{n}問")
        aa, k2 = synth(f"正解は、{q['yomi']}！")
        q_end = 0.15 + len(qa) / SR
        cd = q_end + 0.15                         # カウントダウン開始
        rev = cd + COUNT                          # 答えを出す瞬間
        end = round((rev + 0.3 + len(aa) / SR + 0.9) * FPS) / FPS
        segs.append(dict(kind="q", q=q, n=n, start=t, end=t + end, cd=cd, rev=rev,
                         voices=[(0.15, qa), (rev + 0.3, aa)],
                         sfx=[(cd + i, "tick") for i in range(COUNT)] + [(rev, "correct1.mp3")], kana=[k1, k2]))
        t += end
    a, kana = synth(ENDING["voice"])
    segs.append(dict(kind="end", start=t, end=t + round((0.2 + len(a) / SR + 1.0) * FPS) / FPS,
                     voices=[(0.2, a)], sfx=[(0.0, "decision52.mp3")], kana=[kana]))
    return segs


# ---- 描画の部品 ---------------------------------------------------------------
_cache = {}


def font(size, weight=b"Black"):
    key = ("f", size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_name(weight)
        _cache[key] = f
    return _cache[key]


def load(name):
    if name not in _cache:
        work, num = name.split("/")
        _cache[name] = Image.open(RAW / work / f"{work}{num}.jpg").convert("RGB")
    return _cache[name]


def cover(name, blur):
    """写真を 9:16 いっぱいに拡大した背景。blur=True で強くぼかして暗くする"""
    key = ("cover", name, blur)
    if key not in _cache:
        im = load(name)
        s = H / im.height
        big = im.resize((round(im.width * s), H), Image.BILINEAR)
        x = (big.width - W) // 2
        big = big.crop((x, 0, x + W, H))
        if blur:
            big = ImageEnhance.Brightness(big.filter(ImageFilter.GaussianBlur(40))).enhance(0.45)
        else:
            big = ImageEnhance.Brightness(big).enhance(0.6)
        _cache[key] = big.convert("RGBA")
    return _cache[key]


def emoji(ch, size):
    key = ("e", ch, size)
    if key not in _cache:
        e = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), ch, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True)
        e = e.crop(e.getbbox())
        _cache[key] = e.resize((size, round(size * e.height / e.width)), Image.LANCZOS)
    return _cache[key]


def outlined(text, size, fill="white", stroke="black"):
    """白文字＋黒フチの 1 行 (絵文字はカラー)"""
    f = font(size)
    sw = max(6, size // 8)
    body = "".join(ch for ch in text if ord(ch) < 0x1F000)
    emo = [ch for ch in text if ord(ch) >= 0x1F000]
    w = int(f.getlength(body)) + sw * 2 + (int(size * 1.1) + 8 if emo else 0)
    im = Image.new("RGBA", (w + 4, int(size * 1.4) + sw * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((sw, sw), body, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    if emo:
        e = emoji(emo[0], int(size * 1.05))
        im.alpha_composite(e, (int(f.getlength(body)) + sw * 2 + 4, sw + int(size * 0.2)))
    return im


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def place(frame, el, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        el = el.resize((max(1, round(el.width * scale)), max(1, round(el.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        el = el.copy()
        el.putalpha(el.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(el, (round(cx - el.width / 2), round(cy - el.height / 2)))


def band(lines, size, color=(20, 20, 20), alpha=200):
    els = [outlined(t, size) for t in lines]
    h = sum(e.height for e in els) + 50
    im = Image.new("RGBA", (W, h), color + (alpha,))
    y = 25
    for e in els:
        im.alpha_composite(e, ((W - e.width) // 2, y))
        y += e.height
    return im


def photo_card(name, w=1000):
    key = ("pc", name, w)
    if key not in _cache:
        im = load(name)
        h = round(w * im.height / im.width)
        card = Image.new("RGBA", (w + 16, h + 16), (255, 255, 255, 255))
        card.paste(im.resize((w, h), Image.LANCZOS), (8, 8))
        _cache[key] = card
    return _cache[key]


def kanji_card(q, revealed_a):
    """白いカードに漢字。答えのときは下に赤字で読みが出る"""
    cw, ch = 900, 470
    im = Image.new("RGBA", (cw + 20, ch + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 14, cw + 10, ch + 14), radius=44, fill=(0, 0, 0, 90))
    d.rounded_rectangle((0, 0, cw, ch), radius=44, fill=(255, 253, 245, 255), outline=(40, 40, 40, 255), width=8)
    size = 250 if len(q["kanji"]) <= 2 else 210
    ky = 205 if revealed_a > 0 else 235
    d.text((cw // 2, ky), q["kanji"], font=font(size), fill=(25, 25, 25), anchor="mm")
    if revealed_a > 0:
        yomi = Image.new("RGBA", (cw, 120), (0, 0, 0, 0))
        ImageDraw.Draw(yomi).text((cw // 2, 60), q["yomi"], font=font(92), fill=RED, anchor="mm")
        place(im, yomi, cw // 2, 395, scale=0.6 + 0.4 * ease_back(revealed_a), alpha=min(1, revealed_a * 2))
    return im


def header(n, stars):
    key = ("h", n, stars)
    if key not in _cache:
        lab = outlined(f"第{n}問", 92, fill=YELLOW)
        st = "★" * stars + "☆" * (5 - stars)
        s = Image.new("RGBA", (420, 80), (0, 0, 0, 0))
        ImageDraw.Draw(s).text((210, 40), st, font=font(60), fill=YELLOW, anchor="mm", stroke_width=5,
                               stroke_fill="black")
        im = Image.new("RGBA", (max(lab.width, s.width), lab.height + s.height), (0, 0, 0, 0))
        im.alpha_composite(lab, ((im.width - lab.width) // 2, 0))
        im.alpha_composite(s, ((im.width - s.width) // 2, lab.height - 6))
        _cache[key] = im
    return _cache[key]


def countdown(left, frac):
    """残り秒数の数字と、減っていく輪"""
    r = 150
    im = Image.new("RGBA", (2 * r + 40, 2 * r + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 20 + 2 * r, 20 + 2 * r), fill=(0, 0, 0, 150), outline=(255, 255, 255, 90), width=14)
    d.arc((20, 20, 20 + 2 * r, 20 + 2 * r), -90, -90 + 360 * frac, fill=YELLOW + (255,), width=14)
    d.text((20 + r, 20 + r), str(left), font=font(190), fill="white", anchor="mm")
    return im


# ---- 1 フレーム ---------------------------------------------------------------
KANJI_CY = 640
LOWER_CY = 1180       # カウントダウン / 答えの写真の中心


def draw(seg, lt):
    if seg["kind"] == "title":
        names = TITLE["imgs"]
        ph = round(W * 1038 / 1920)
        frame = Image.new("RGBA", (W, H), (10, 10, 10, 255))
        top = (H - 3 * ph - 24) // 2
        z = 1 + 0.06 * min(lt / 4, 1)
        for k, name in enumerate(names):
            im = load(name)
            cw, chh = im.width / z, im.height / z
            p = im.resize((W, ph), Image.BICUBIC, box=((im.width - cw) / 2, (im.height - chh) / 2,
                                                       (im.width + cw) / 2, (im.height + chh) / 2))
            frame.paste(p, (0, top + k * (ph + 12)))
        place(frame, band(TITLE["telop"], 104, color=(150, 20, 20), alpha=225), W / 2, H / 2,
              scale=0.7 + 0.3 * ease_back(lt / 0.3), alpha=min(1, lt * 5))
        return frame.convert("RGB")

    if seg["kind"] == "end":
        frame = cover(ENDING["img"], False).copy()
        place(frame, band(ENDING["telop"], 96), W / 2, H / 2, scale=0.7 + 0.3 * ease_back(lt / 0.3),
              alpha=min(1, lt * 5))
        return frame.convert("RGB")

    q, n = seg["q"], seg["n"]
    rev = seg["rev"]
    ra = (lt - rev) / 0.3                      # 答えの出具合 (0→1)
    frame = cover(q["img"], True).copy()
    if ra > 0:                                 # 答えの瞬間、背景が少し明るくなる
        frame = Image.blend(frame, cover(q["img"], False), min(1, ra) * 0.35)
    place(frame, header(n, q["stars"]), SAFE_RIGHT / 2 + 20, 270, scale=0.7 + 0.3 * ease_back(lt / 0.25))
    place(frame, kanji_card(q, max(0.0, min(1.0, ra))), W / 2, KANJI_CY, scale=0.6 + 0.4 * ease_back(lt / 0.3))
    if seg["cd"] <= lt < rev:
        el = lt - seg["cd"]
        left = COUNT - int(el)
        sub = el - int(el)
        place(frame, countdown(left, 1 - el / COUNT), SAFE_RIGHT / 2 + 20, LOWER_CY,
              scale=1.25 - 0.25 * ease_back(sub / 0.2))
    elif lt < seg["cd"]:
        place(frame, outlined("読める？", 96), SAFE_RIGHT / 2 + 20, LOWER_CY, alpha=min(1, lt * 4))
    if ra > 0:
        p = ease_back(ra)
        card = photo_card(q["img"], w=860)
        place(frame, card, SAFE_RIGHT / 2 + 20, LOWER_CY + 30, scale=0.6 + 0.4 * p, alpha=min(1, ra * 2))
        tag = outlined(f"『{q['work']}』", 54)
        place(frame, tag, SAFE_RIGHT / 2 + 20, LOWER_CY + 290, alpha=min(1, ra * 2))
        if ra < 1:                             # 「ピンポン」の瞬間に白く光る
            frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(160 * (1 - ra)))))
    return frame.convert("RGB")


def render_frame(t, segs, total):
    seg = next(s for s in reversed(segs) if s["start"] <= t + 1e-9)
    frame = draw(seg, t - seg["start"])
    if t > total - 0.4:                        # ループ再生でつながるよう、最後は冒頭へ
        a = min(1, (t - (total - 0.4)) / (0.4 - 1 / FPS))
        frame = Image.blend(frame, draw(segs[0], 0.0), a)
    return frame


# ---- 音声 -------------------------------------------------------------------
def load_sfx(name):
    if name == "tick":                        # カウントダウンの「カチッ」は自前で合成
        t = np.arange(int(SR * 0.06)) / SR
        return (np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 70)) * 0.8
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(SFX_DIR / name), "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 50):] if len(idx) else a


def active_rms(a):
    act = a[np.abs(a) > 0.02]
    return np.sqrt(np.mean(act ** 2)) if len(act) else 1e-9


def make_audio(segs, total):
    buf = np.zeros(int(SR * total) + SR)
    voice = np.zeros_like(buf)
    for s in segs:
        for off, clip in s["voices"]:
            a = int((s["start"] + off) * SR)
            voice[a:a + len(clip)] += clip
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    target = active_rms(voice) * 10 ** (SFX_DB / 20)
    for s in segs:
        for off, name in s["sfx"]:
            clip = load_sfx(name)
            clip = clip * target / active_rms(clip) * (0.8 if name == "tick" else 1.0)
            a = int((s["start"] + off) * SR)
            buf[a:a + len(clip)] += clip[: len(buf) - a]
    path = OUT / "_quiz_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(path)
    return path


def main():
    OUT.mkdir(exist_ok=True)
    segs = build_timeline()
    total = segs[-1]["end"]
    wav = make_audio(segs, total)
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart",
           str(OUT / "ghibli_kanji_quiz.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(round(total * FPS)):
        proc.stdin.write(render_frame(i / FPS, segs, total).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(total=round(total, 3),
                segs=[dict(kind=s["kind"], start=round(s["start"], 3), end=round(s["end"], 3),
                           rev=round(s["start"] + s["rev"], 3) if "rev" in s else None, kana=s["kana"])
                      for s in segs])
    (OUT / "ghibli_kanji_quiz_timeline.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
