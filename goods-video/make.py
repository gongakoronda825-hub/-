"""TikTok ジブリグッズ紹介「ガチで買ってよかったジブリグッズ3選」のテンプレート

写真は raw/sample/ の仮の画像。実物の写真に差し替えるときは CUTS の img を変える。
TikTok で伸びている購入品紹介の作りを取り入れている:
  ・チェキ風に少し傾けた写真カード＋マスキングテープ、ポンッと弾んで登場
  ・丸い値段シール、1 行ずつ弾んで出るテロップ ({ } で囲んだ言葉は黄色)
  ・順位発表は大きな文字＋キラキラ＋画面の揺れ＋白フラッシュ＋「ドドン」
  ・締めは「保存して見返してね」
使い方: python3 goods-video/make.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
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
PAUSE = 0.5
LEAD = 0.2           # テロップ・写真を出してからナレーションまで
RANK_LEAD = 0.7      # 順位発表は「ドドン」を聞かせてから
TAIL = 0.25
SFX_DB = -12
SAFE_BOTTOM = int(H * 0.80)   # ここより下は TikTok の説明文・ボタンと重なる
SAFE_RIGHT = int(W * 0.85)    # 右端 15% はいいね・コメントのボタン

GREEN = (38, 96, 56)
YELLOW = (255, 214, 0)
RED = (232, 67, 58)
RANK_COLOR = {"第3位": (196, 120, 60), "第2位": (128, 140, 165), "第1位": (232, 176, 20)}

# ---- カット -----------------------------------------------------------------
# telop: 1 行ずつ弾んで出る。{ } で囲んだ部分は黄色。 price: 値段シール。 tilt: 写真カードの傾き(度)
CUTS = [
    dict(name="① つかみ", kind="title", imgs=["sample/003", "sample/002", "sample/001"],
         telop=["{ガチで}買ってよかった", "ジブリグッズ3選✨"], teaser="最後の1位が神すぎた…",
         voice="ガチで買ってよかった、ジブリグッズ3選！最後の1位は、神すぎました",
         sfx=[(0.0, "question1.mp3")]),
    dict(name="② 第3位", kind="rank", rank="第3位", img="sample/003", tilt=-3, price="◯◯円",
         telop=["グッズC"],
         voice="第3位は、グッズシー。お値段は、まるまる円です",
         sfx=[(0.0, "drum-japanese2.mp3"), (0.9, "decision22.mp3")]),
    dict(name="③ 第3位の推し", kind="item", img="sample/003", tilt=2, label="第3位",
         telop=["✅ {推しポイント①}", "✅ {推しポイント②}"],
         voice="推しポイントは、ここに2つ入ります",
         sfx=[(-0.1, "highspeed-movement1.mp3")]),
    dict(name="④ 第2位", kind="rank", rank="第2位", img="sample/002", tilt=3, price="◯◯円",
         telop=["グッズB"],
         voice="第2位は、グッズビー。お値段は、まるまる円",
         sfx=[(0.0, "drum-japanese2.mp3"), (0.9, "decision22.mp3")]),
    dict(name="⑤ 第2位の推し", kind="item", img="sample/002", tilt=-2, label="第2位",
         telop=["✅ {使ってわかった良さ}", "✅ {ここが最高}"],
         voice="実際に使ってわかった良いところを、ここで紹介します",
         sfx=[(-0.1, "highspeed-movement1.mp3")]),
    dict(name="⑥ 第1位", kind="rank", rank="第1位", img="sample/001", tilt=-3, price="◯◯円",
         telop=["グッズA"],
         voice="そして第1位は、グッズエー。お値段は、まるまる円",
         sfx=[(0.0, "drum-japanese2.mp3"), (0.9, "decision22.mp3")]),
    dict(name="⑦ 第1位の推し", kind="item", img="sample/001", tilt=2, label="第1位",
         telop=["✅ {毎日使うほどお気に入り}", "✅ {ここが神}"],
         voice="毎日使うほどお気に入りの理由が、ここに入ります",
         sfx=[(-0.1, "highspeed-movement1.mp3"), (0.4, "eye-shine1.mp3")]),
    dict(name="⑧ 締め", kind="end", img="sample/004", tilt=-2,
         telop=["あなたの推しグッズは？", "{コメント}で教えてね💬"],
         voice="あなたの推しジブリグッズは？コメントで教えてね。保存して、見返してね",
         sfx=[(0.0, "decision52.mp3")]),
]


# ---- ナレーション -------------------------------------------------------------
def post(path, params, body=b""):
    req = urllib.request.Request(f"{ENGINE}{path}?{urllib.parse.urlencode(params)}", data=body,
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def synth(text):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    for ap in q["accent_phrases"]:          # 子音が短すぎて聞こえなくなるのを防ぐ
        for m in ap["moras"]:
            if m.get("consonant") and m["consonant_length"] < 0.045:
                m["consonant_length"] = 0.045
    q.update(speedScale=SPEED, pauseLengthScale=PAUSE, prePhonemeLength=0.0, postPhonemeLength=0.05,
             outputSamplingRate=SR, outputStereo=False)
    with wave.open(io.BytesIO(post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode()))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return a[idx[0]: idx[-1] + 1] if len(idx) else a, q["kana"]


def build_timeline():
    t = 0.0
    for c in CUTS:
        c["audio"], c["kana"] = synth(c["voice"])
        c["start"] = t
        c["voice_start"] = t + (RANK_LEAD if c["kind"] == "rank" else LEAD)
        c["end"] = round((c["voice_start"] + len(c["audio"]) / SR + TAIL) * FPS) / FPS
        t = c["end"]
    return t


# ---- 描画の部品 ---------------------------------------------------------------
BG = Image.open(HERE / "assets" / "bg_grid.jpg").convert("RGB").resize((W, H))
_cache = {}


def font(size, weight=b"Black"):
    key = ("font", size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_name(weight)
        _cache[key] = f
    return _cache[key]


def emoji(ch, size):
    key = ("emoji", ch, size)
    if key not in _cache:
        e = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), ch, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True)
        e = e.crop(e.getbbox())
        _cache[key] = e.resize((size, round(size * e.height / e.width)), Image.LANCZOS)
    return _cache[key]


def load(name):
    if name not in _cache:
        work, num = name.split("/")
        _cache[name] = Image.open(RAW / work / f"{work}{num}.jpg").convert("RGB")
    return _cache[name]


def ease_back(x):
    """0→1 で少し行き過ぎて戻る (ポンッと弾む)"""
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def place(frame, el, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    """RGBA の部品を中心 (cx, cy) に、拡大・回転・透明度をつけて貼る"""
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        el = el.resize((max(1, round(el.width * scale)), max(1, round(el.height * scale))), Image.BICUBIC)
    if angle:
        el = el.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        el = el.copy()
        el.putalpha(el.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(el, (round(cx - el.width / 2), round(cy - el.height / 2)))


def is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF   # 絵文字だけ (日本語の文字は含まない)


def text_line(line, size, fill="white", stroke="black"):
    """1 行のテロップ。{ } の中は黄色、絵文字はカラー"""
    f = font(size)
    sw = max(6, size // 7)
    parts, x, color = [], 0, fill
    for ch in line:
        if ch == "{":
            color = YELLOW
            continue
        if ch == "}":
            color = fill
            continue
        if is_emoji(ch):
            e = emoji(ch, int(size * 1.05))
            parts.append(("e", e, x))
            x += e.width + 6
        elif ch == "️":
            continue
        else:
            parts.append(("t", (ch, color), x))
            x += f.getlength(ch)
    im = Image.new("RGBA", (int(x) + sw * 2 + 6, int(size * 1.35) + sw * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for kind, v, px in parts:
        if kind == "t":
            d.text((sw + px, sw), v[0], font=f, fill=v[1], stroke_width=sw, stroke_fill=stroke)
    for kind, v, px in parts:
        if kind == "e":
            im.alpha_composite(v, (int(sw + px), int(sw + size * 0.18)))
    return im


def pill(el, color=GREEN, alpha=230, pad=(34, 14), radius=40):
    """テロップの行を、角の丸いシール風のパネルに乗せる"""
    p = Image.new("RGBA", (el.width + pad[0] * 2, el.height + pad[1] * 2), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, p.height - 1), radius=radius, fill=color + (alpha,))
    p.alpha_composite(el, pad)
    return p


def fit(el, max_w):
    return el if el.width <= max_w else el.resize((max_w, round(el.height * max_w / el.width)), Image.LANCZOS)


def polaroid(photo_name, t, w=760):
    """チェキ風カード: 白い枠 (下を太く)＋マスキングテープ＋影。写真の中はゆっくりズーム"""
    im = load(photo_name)
    z = 1 + 0.06 * min(t / 4.0, 1)
    ph = round(w * im.height / im.width)
    cw, ch = im.width / z, im.height / z
    photo = im.resize((w, ph), Image.BICUBIC, box=((im.width - cw) / 2, (im.height - ch) / 2,
                                                   (im.width + cw) / 2, (im.height + ch) / 2))
    m, mb = 26, 90
    card = Image.new("RGBA", (w + 2 * m + 60, ph + m + mb + 60), (0, 0, 0, 0))
    sh = Image.new("L", card.size, 0)
    ImageDraw.Draw(sh).rectangle((36, 42, 30 + w + 2 * m + 6, 30 + ph + m + mb + 12), fill=120)
    card.paste((30, 50, 30, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(card).rectangle((30, 30, 30 + w + 2 * m, 30 + ph + m + mb), fill=(255, 255, 255, 255))
    card.paste(photo, (30 + m, 30 + m))
    tape = Image.new("RGBA", (200, 56), (255, 236, 150, 190))
    for i in range(0, 200, 24):  # テープの斜めストライプ
        ImageDraw.Draw(tape).line([(i, 0), (i + 20, 56)], fill=(255, 255, 255, 70), width=8)
    for x, ang in ((70, 32), (card.width - 70, -32)):
        tp = tape.rotate(ang, expand=True, resample=Image.BICUBIC)
        card.alpha_composite(tp, (x - tp.width // 2, 34 - tp.height // 2))
    return card


def price_tag(text):
    key = ("price", text)
    if key not in _cache:
        r = 128
        im = Image.new("RGBA", (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((14, 18, 14 + 2 * r, 18 + 2 * r), fill=(0, 0, 0, 70))
        d.ellipse((10, 10, 10 + 2 * r, 10 + 2 * r), fill=RED + (255,), outline=(255, 255, 255, 255), width=8)
        d.text((10 + r, 10 + r - 34), "お値段", font=font(38, b"Bold"), fill="white", anchor="mm")
        d.text((10 + r, 10 + r + 22), text, font=font(52), fill="white", anchor="mm")
        _cache[key] = im
    return _cache[key]


def rank_text(text):
    key = ("rank", text)
    if key not in _cache:
        f = font(210)
        w = int(f.getlength(text)) + 80
        im = Image.new("RGBA", (w, 290), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((w // 2, 145), text, font=f, fill=RANK_COLOR[text], anchor="mm",
                                stroke_width=16, stroke_fill="black")
        _cache[key] = im
    return _cache[key]


def small_rank(text):
    key = ("srank", text)
    if key not in _cache:
        el = text_line(text, 64, fill=RANK_COLOR[text])
        _cache[key] = el
    return _cache[key]


def teaser_tag(text):
    el = text_line(text, 58)
    return pill(el, color=RED, alpha=255, pad=(30, 10), radius=20)


# ---- 1 フレーム ---------------------------------------------------------------
CARD_CY = 820            # 写真カードの中心
CARD_CX = (SAFE_RIGHT + 20) // 2   # 右端 15% (ボタン) にかからないよう少し左寄せ
TELOP_Y0 = 1215          # テロップ 1 行目の中心


def draw_telop(frame, c, lt, y0=TELOP_Y0, gap=118, delay=0.0, size=72):
    for i, line in enumerate(c["telop"]):
        el = fit(pill(text_line(line, size)), SAFE_RIGHT - 60)
        p = ease_back((lt - delay - i * 0.22) / 0.28)
        place(frame, el, (SAFE_RIGHT + 20) / 2 + 10, y0 + i * gap, scale=0.6 + 0.4 * p, alpha=min(1, p * 1.5))


def cut_frame(c, lt):
    frame = BG.copy().convert("RGBA")
    shake = (0, 0)
    if c["kind"] == "rank" and lt < 0.35:    # 順位発表で画面が揺れる
        a = 22 * (1 - lt / 0.35)
        shake = (a * math.sin(lt * 90), a * math.cos(lt * 70))

    if c["kind"] == "title":
        pos = [(270, 430, -7, 420), (680, 470, 6, 420), (460, 1390, -3, 600)]   # (x, y, 傾き, 幅)
        for k, (name, (x, y, ang, w)) in enumerate(zip(c["imgs"], pos)):
            p = ease_back((lt - k * 0.12) / 0.3)
            place(frame, polaroid(name, lt, w=w), x, y, scale=0.5 + 0.5 * p, angle=ang, alpha=min(1, p * 2))
        band_p = ease_back((lt - 0.25) / 0.3)
        lines = [text_line(line, 104) for line in c["telop"]]
        for i, el in enumerate(lines):
            place(frame, fit(pill(el, alpha=235), SAFE_RIGHT - 40), CARD_CX, 830 + i * 180, scale=0.7 + 0.3 * band_p,
                  alpha=min(1, band_p * 2))
        tp = ease_back((lt - 0.9) / 0.3)
        place(frame, teaser_tag(c["teaser"]), CARD_CX, 1150, scale=tp, angle=-3)
        for k, (x, y) in enumerate(((120, 700), (960, 1080))):   # キラキラが揺れる
            place(frame, emoji("✨", 110), x, y + 12 * math.sin(lt * 4 + k), alpha=min(1, lt * 3))
        return frame.convert("RGB")

    # 写真カード
    p = ease_back(lt / 0.32)
    place(frame, polaroid(c["img"], lt), CARD_CX + shake[0], CARD_CY + shake[1], scale=0.75 + 0.25 * p,
          angle=c.get("tilt", 0), alpha=min(1, p * 2))

    if c["kind"] == "rank":
        r = ease_back(lt / 0.25)
        place(frame, rank_text(c["rank"]), W / 2 + shake[0], 300 + shake[1], scale=1.6 - 0.6 * r)
        for k, x in enumerate((150, 930)):
            place(frame, emoji("✨", 120), x, 290 + 14 * math.sin(lt * 5 + k * 2), alpha=min(1, lt * 4))
        tp = ease_back((lt - 0.85) / 0.3)
        place(frame, price_tag(c["price"]), CARD_CX + 300, 560, scale=tp, angle=12)
        draw_telop(frame, c, lt, delay=0.1, size=96)
    elif c["kind"] == "item":
        place(frame, small_rank(c["label"]), 190, 330, angle=4)
        draw_telop(frame, c, lt)
    else:  # end
        draw_telop(frame, c, lt)
        sp = ease_back((lt - 0.6) / 0.3)
        place(frame, teaser_tag("保存して見返してね📌"), W / 2, 330, scale=sp, angle=-3)

    if c["kind"] == "rank" and lt < 0.3:     # 白フラッシュ
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - lt / 0.3) ** 1.5))))
    return frame.convert("RGB")


def render_frame(t, total):
    k = max(i for i, c in enumerate(CUTS) if c["start"] <= t + 1e-9)
    frame = cut_frame(CUTS[k], t - CUTS[k]["start"])
    if t > total - 0.4:  # 最後は①の頭へ戻してループでつながるように
        a = min(1, (t - (total - 0.4)) / (0.4 - 1 / FPS))
        frame = Image.blend(frame, cut_frame(CUTS[0], 0.0), a)
    return frame


# ---- 音声 -------------------------------------------------------------------
def load_sfx(name):
    path = SFX_DIR / name
    if not path.exists():  # 効果音ラボの素材は再配布禁止なので、無ければサイトから取る
        cat = {"drum-japanese2.mp3": "anime", "question1.mp3": "anime", "eye-shine1.mp3": "anime",
               "highspeed-movement1.mp3": "battle"}.get(name, "button")
        SFX_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sSf", "-A", "Mozilla/5.0", "-e", f"https://soundeffect-lab.info/sound/{cat}/",
                        "-o", str(path), f"https://soundeffect-lab.info/sound/{cat}/mp3/{name}"], check=True)
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 50):] if len(idx) else a


def active_rms(a):
    act = a[np.abs(a) > 0.02]
    return np.sqrt(np.mean(act ** 2)) if len(act) else 1e-9


def make_audio(total):
    buf = np.zeros(int(SR * total) + SR)
    voice = np.zeros_like(buf)
    for c in CUTS:
        a = int(c["voice_start"] * SR)
        voice[a:a + len(c["audio"])] += c["audio"]
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    target = active_rms(voice) * 10 ** (SFX_DB / 20)
    events = []
    for c in CUTS:
        for off, name in c["sfx"]:
            t = max(0.0, c["start"] + off)
            clip = load_sfx(name)
            clip = clip * target / active_rms(clip)
            a = int(t * SR)
            buf[a:a + len(clip)] += clip[: len(buf) - a]
            events.append((round(t, 2), name))
    path = OUT / "_goods_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(path)
    return path, events


def main():
    OUT.mkdir(exist_ok=True)
    total = build_timeline()
    wav, events = make_audio(total)
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart",
           str(OUT / "goods_sample.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(round(total * FPS)):
        proc.stdin.write(render_frame(i / FPS, total).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(total=round(total, 3), sfx=events,
                cuts=[dict(name=c["name"], start=round(c["start"], 3), end=round(c["end"], 3),
                           voice_start=round(c["voice_start"], 3), kana=c["kana"]) for c in CUTS])
    (OUT / "goods_sample_timeline.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
