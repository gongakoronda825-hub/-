"""千と千尋の神隠し 雑学ショート — ナレーション生成から動画書き出しまで

1. VOICEVOX (http://localhost:50021) で各カットのナレーションを作る
2. ナレーションの長さからカットの長さを決める (前 0.2 秒でテロップ、後ろ 0.3 秒の余白)
3. 1080x1920 / 30fps の映像を描き、ナレーション＋効果音と合わせて output/chihiro_trivia.mp4 に書き出す

使い方: python3 chihiro-video/make.py
"""
import io
import json
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "chihiro"
OUT = ROOT / "output"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = ROOT / "ghibli-video" / "fonts" / "NotoSansJP.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS, SR = 1080, 1920, 30, 44100
ENGINE = "http://localhost:50021"
SPEAKER = 2          # 四国めたん ノーマル
SPEED = 1.1
PAUSE = 0.5          # 「、」「。」での間 (1.0 が標準)
LEAD = 0.2           # テロップをナレーションより早く出す秒数
TAIL = 0.3           # ナレーション後の余白
XFADE = 0.25         # カット間のクロスフェード
LOOP_FADE = 0.5      # 最後に①の画像へ戻すフェード
ZOOM = 0.08          # 100% → 108%
SFX_DB = -12         # 効果音はナレーションより 12dB 下げる

# 写真は画面の上下中央。テロップは写真のすぐ下 (右端 15% と下 20% は避ける)
PIC_TOP = (H - round(W * 1038 / 1920)) // 2
TELOP_TOP = PIC_TOP + round(W * 1038 / 1920) + 24
TELOP_CX = int(W * 0.85 / 2) + 20   # 左端 40px〜右端 15% 手前の中央
TELOP_MAX_W = int(W * 0.85) - 80
# 題名 (カット①) だけは写真の上に大きく。画面上部には TikTok のボタンがないので横幅いっぱいに使う
TITLE_MAX_W = W - 80
TITLE_BOTTOM = PIC_TOP - 40

# ---- カット定義 ------------------------------------------------------------
# layout "crop": 9:16 に切り抜く。focus=(x, y) 元画像での顔の位置, face_y=出力での顔の高さ(比率), crop_h=切り抜く高さ
# layout "blur": ぼかした同じ画像を背景に敷き、元画像を top の位置に置く
#   box=(x0, 幅) を指定すると、元画像をその範囲で正方形に切り抜いて置く (顔のアップ用。
#   9:16 に切り抜くと顔がテロップ帯 (上から35〜45%) にかかってしまうため)
CUTS = [
    dict(name="① 題名", img="chihiro001", title=True,
         telop=["千と千尋は", "“10歳の女の子たち”の", "ために作られた"],
         voice="千と千尋は、10歳の女の子たちのために作られた映画なんです",
         sfx=[("start", "question1.mp3")]),
    dict(name="② きっかけ", img="chihiro002",
         telop=["宮崎監督の山小屋に", "毎年来ていた", "友人の娘たち（当時10歳）"],
         voice="宮崎監督の山小屋に毎年遊びに来ていた、友人の娘さんたち。当時みんな10歳でした",
         sfx=[("cut_in", "highspeed-movement1.mp3")]),
    dict(name="③ 監督の思い", img="chihiro018",
         telop=["「あなたたちのための", "映画」を作りたい", "だから千尋も同じ10歳"],
         voice="監督は、あなたたちのための映画だ、と言える作品を作りたかった。だから主人公の千尋も、同じ10歳の女の子なんです",
         sfx=[("start", "decision22.mp3")]),
    dict(name="④ 序盤", img="chihiro004", badge="序盤",
         telop=["特別な力のない普通の子", "ふてくされて", "お母さんにくっついてばかり"],
         voice="特別な力なんてない、普通の女の子。序盤は、ふてくされて、お母さんにくっついてばかり",
         sfx=[("cut_in", "highspeed-movement1.mp3")]),
    dict(name="⑤ 序盤", img="chihiro023", badge="序盤",
         telop=["知らない世界で", "不安で泣いてしまう"],
         voice="知らない世界で、不安で泣いてしまう女の子でした",
         sfx=[("cut_in", "highspeed-movement1.mp3")]),
    dict(name="⑥ 転機", img="chihiro017",
         telop=["湯婆婆に", "「ここで働かせてください」", "ここから変わり始める"],
         voice="でも、湯婆婆に、ここで働かせてください、と頼み続けたところから、少しずつ変わっていきます",
         sfx=[("start", "question1.mp3")]),
    dict(name="⑦ 終盤", img="chihiro042", badge="終盤",
         telop=["ハクを助けるため", "ひとりで電車に乗り", "銭婆のもとへ"],
         voice="終盤では、ハクを助けるために、ひとりで電車に乗って、ゼニーバのもとへ",
         sfx=[("start", "eye-shine1.mp3")]),
    dict(name="⑧ 終盤", img="chihiro047", badge="終盤",
         telop=["湯婆婆の難題にも", "自分の力で答えを出す"],
         voice="最後は、湯婆婆の出した難題にも、自分の力で答えを出します",
         sfx=[("cut_in", "highspeed-movement1.mp3")]),
    dict(name="⑨ 締め", img="chihiro001", img2="chihiro050", badge="序盤", badge2="終盤", swap_at=0.3,
         telop=["同じ子とは思えない", "“顔つきの変化”に注目👀"],
         voice="同じ女の子とは思えないほどの、顔つきの変化。次に観るときは、ぜひ注目してみてください",
         sfx=[("swap", "eye-shine1.mp3"), ("start", "decision52.mp3")]),
]
for _c in CUTS:              # 全カット: ぼかし背景＋元の写真を画面の上下中央に
    _c.update(layout="blur", top=PIC_TOP)
SWAP_AT = 0.45       # ④ で 2 枚目に切り替える位置 (カット内の比率)
SWAP_LEN = 0.6


# ---- ナレーション (VOICEVOX) ------------------------------------------------
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
        dur = len(c["audio"]) / SR
        c["start"] = t
        c["voice_start"] = t + LEAD
        c["end"] = round((c["voice_start"] + dur + TAIL) * FPS) / FPS
        t = c["end"]
    return t


# ---- 映像 -------------------------------------------------------------------
_img = {}


def load(name):
    if name not in _img:
        _img[name] = Image.open(RAW / f"{name}.jpg").convert("RGB")
    return _img[name]


def crop_frame(name, focus, face_y, crop_h, z):
    """顔 (focus) を出力の face_y の高さに置いて 9:16 に切り抜く。z でズーム"""
    im = load(name)
    ch = crop_h / z
    cw = ch * W / H
    fx, fy = focus
    x0 = min(max(fx - cw / 2, 0), im.width - cw)
    y0 = min(max(fy - face_y * ch, 0), im.height - ch)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


_bg = {}


def blur_frame(name, top, z, box=None):
    im = load(name)
    if name not in _bg:
        s = H / im.height
        big = im.resize((round(im.width * s), H), Image.BILINEAR)
        x = (big.width - W) // 2
        big = big.crop((x, 0, x + W, H)).filter(ImageFilter.GaussianBlur(36))
        _bg[name] = ImageEnhance.Brightness(big).enhance(0.55)
    frame = _bg[name].copy()
    bx, bw = box if box else (0, im.width)
    fh = round(W * im.height / bw)
    cw, ch = bw / z, im.height / z
    cx, cy = bx + (bw - cw) / 2, (im.height - ch) / 2
    frame.paste(im.resize((W, fh), Image.BICUBIC, box=(cx, cy, cx + cw, cy + ch)), (0, top))
    return frame


def picture(c, lt, dur, which=1):
    z = 1 + ZOOM * min(max(lt / dur, 0), 1)
    if c["layout"] == "blur":
        if which == 2:
            return blur_frame(c["img2"], c["top"], z, c.get("box2"))
        return blur_frame(c["img"], c["top"], z, c.get("box"))
    return crop_frame(c["img"], c["focus"], c["face_y"], c["crop_h"], z)


def is_emoji(ch):
    return ord(ch) >= 0x1F300


def telop_image(lines, size):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(b"Black")
    ef = ImageFont.truetype(EMOJI_FONT, 109)
    sw = max(6, size // 8)
    lh = int(size * 1.3)
    rendered = []
    for line in lines:
        parts, x = [], 0
        for ch in line:
            if is_emoji(ch):
                e = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
                ImageDraw.Draw(e).text((0, 0), ch, font=ef, embedded_color=True)
                e = e.crop(e.getbbox()).resize((int(size * 1.25), int(size * 1.25 * 90 / 120)), Image.LANCZOS)
                parts.append(("img", e, x))
                x += e.width + 4
            else:
                w = f.getlength(ch)
                parts.append(("txt", ch, x))
                x += w
        rendered.append((parts, x))
    width = int(max(w for _, w in rendered)) + sw * 2 + 8
    im = Image.new("RGBA", (width, lh * len(lines) + sw * 2 + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (parts, w) in enumerate(rendered):
        ox = (width - w) / 2
        y = sw + i * lh
        for kind, v, x in parts:
            if kind == "txt":
                d.text((ox + x, y), v, font=f, fill="white", stroke_width=sw, stroke_fill="black")
        for kind, v, x in parts:
            if kind == "img":
                im.alpha_composite(v, (int(ox + x), int(y + size * 0.3)))
    return im


def title_size():
    c = next(c for c in CUTS if c.get("title"))
    size = 110
    while telop_image(c["telop"], size).width > TITLE_MAX_W:
        size -= 2
    return size


def fit_size():
    """全カットで同じ文字サイズ。一番長い行が幅に収まる大きさにする"""
    size = 80
    while size > 30:
        if all(telop_image(c["telop"], size).width <= TELOP_MAX_W for c in CUTS if not c.get("title")):
            return size
        size -= 2
    return size


BADGE_COLOR = {"序盤": (47, 111, 214), "終盤": (240, 130, 30)}
BADGES = {}


def make_badges():
    f = ImageFont.truetype(str(FONT), 60)
    f.set_variation_by_name(b"Black")
    for text, color in BADGE_COLOR.items():
        label = f"{text}の千尋"
        w = int(f.getlength(label)) + 56
        im = Image.new("RGBA", (w, 96), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, 95), radius=22, fill=color + (255,), outline=(255, 255, 255, 255), width=5)
        d.text((w // 2, 46), label, font=f, fill="white", anchor="mm")
        BADGES[text] = im


def cut_frame(k, t):
    """カット k を絶対時刻 t で描く (クロスフェードのため前後にはみ出してもよい)"""
    c = CUTS[k]
    lt = t - c["start"]
    dur = c["end"] - c["start"]
    if "img2" in c:
        s0 = dur * c.get("swap_at", SWAP_AT) - SWAP_LEN / 2
        a = min(max((lt - s0) / SWAP_LEN, 0), 1)
        frame = picture(c, lt, dur, 1)
        if a > 0:
            frame = Image.blend(frame, picture(c, lt, dur, 2), a)
    else:
        a = 0
        frame = picture(c, lt, dur)
    frame = frame.convert("RGBA")
    if c.get("badge"):  # 写真の左上に【序盤】【終盤】ラベル。切り替えのあるカットは途中で差し替え
        label = c["badge2"] if (c.get("badge2") and a >= 0.5) else c["badge"]
        b = BADGES[label]
        frame.alpha_composite(b, (32, PIC_TOP - b.height - 20))
    a = min(max(lt / 0.12, 0), 1)  # テロップはカット頭 (ナレーションの 0.2 秒前) に出す
    if a > 0:
        tl = c["telop_img"]
        if a < 1:
            tl = tl.copy()
            tl.putalpha(tl.getchannel("A").point(lambda v: int(v * a)))
        if c.get("title"):
            frame.alpha_composite(tl, (W // 2 - tl.width // 2, TITLE_BOTTOM - tl.height))
        else:
            frame.alpha_composite(tl, (TELOP_CX - tl.width // 2, TELOP_TOP))
    return frame.convert("RGB")


def render_frame(t, total):
    k = max(i for i, c in enumerate(CUTS) if c["start"] <= t + 1e-9)
    frame = cut_frame(k, t)
    # 次のカットとのクロスフェード (境目をまたいで XFADE 秒)
    if k + 1 < len(CUTS) and t > CUTS[k]["end"] - XFADE / 2:
        a = (t - (CUTS[k]["end"] - XFADE / 2)) / XFADE
        frame = Image.blend(frame, cut_frame(k + 1, t), a)
    if k > 0 and t < CUTS[k]["start"] + XFADE / 2:
        a = (t - (CUTS[k]["start"] - XFADE / 2)) / XFADE
        frame = Image.blend(cut_frame(k - 1, t), frame, a)
    # 最後の 0.5 秒で ①の最初のフレームへ (ループ再生でつながる)
    if t > total - LOOP_FADE:
        a = (t - (total - LOOP_FADE)) / (LOOP_FADE - 1 / FPS)  # 最後のフレームで①の頭と完全に一致
        frame = Image.blend(frame, cut_frame(0, 0.0), min(a, 1))
    return frame


# ---- 音声 -------------------------------------------------------------------
def load_sfx(name):
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(HERE / "sfx" / name), "-f", "s16le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 50):] if len(idx) else a


def active_rms(a):
    env = np.abs(a)
    act = a[env > 0.02]
    return np.sqrt(np.mean(act ** 2)) if len(act) else 1e-9


def make_audio(total):
    buf = np.zeros(int(SR * total) + SR)
    voice = np.zeros_like(buf)
    for c in CUTS:
        a = int(c["voice_start"] * SR)
        voice[a:a + len(c["audio"])] += c["audio"]
    voice *= 10 ** (-13 / 20) / active_rms(voice)          # 話し声の平均を -13dBFS に
    buf += voice
    target = active_rms(voice) * 10 ** (SFX_DB / 20)
    events = []
    for k, c in enumerate(CUTS):
        for when, name in c["sfx"]:
            if when == "start":
                t = c["start"]
            elif when == "cut_in":                           # 切り替わりの瞬間に「シュッ」が来るよう少し前から
                t = max(0.0, c["start"] - 0.12)
            else:                                            # ④ の 2 枚目への切り替え
                d = c["end"] - c["start"]
                t = c["start"] + d * c.get("swap_at", SWAP_AT) - 0.1
            clip = load_sfx(name)
            clip = clip * target / active_rms(clip)
            a = int(t * SR)
            buf[a:a + len(clip)] += clip[: len(buf) - a]
            events.append((round(t, 2), name))
    buf = buf[: int(SR * total)]
    path = OUT / "_chihiro_mix.f32"          # 32bit float のまま渡し、ffmpeg のリミッターで頭だけ抑える
    buf.astype("<f4").tofile(path)
    return path, events


def main():
    OUT.mkdir(exist_ok=True)
    total = build_timeline()
    size = fit_size()
    for c in CUTS:
        c["telop_img"] = telop_image(c["telop"], title_size() if c.get("title") else size)
    make_badges()
    wav, events = make_audio(total)

    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "alimiter=limit=0.89:level=false", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
           "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUT / "chihiro_trivia.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = round(total * FPS)
    for i in range(n):
        proc.stdin.write(render_frame(i / FPS, total).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()

    info = dict(total=round(total, 3), font_size=size, sfx=events,
                cuts=[dict(name=c["name"], img=c["img"], img2=c.get("img2"), start=round(c["start"], 3),
                           end=round(c["end"], 3), voice_start=round(c["voice_start"], 3),
                           voice_end=round(c["voice_start"] + len(c["audio"]) / SR, 3), kana=c["kana"])
                      for c in CUTS])
    (OUT / "chihiro_timeline.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
