"""舞台『千と千尋の神隠し』TikTok動画（1080x1920 / 30fps / 21秒）を書き出す。

使い方: python3 render.py <poster.jpg> <intro.jpg> <舞台映像のコマのフォルダ> <fontdir> <sfx.wav> <out.mp4> [preview秒,...]

舞台映像のコマは、4.5秒・30fps（135枚）に合わせて c_001.jpg〜 の名前で書き出しておく（README 参照）。
"""
import glob
import math
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
GOLD = (236, 200, 120)
WHITE = (255, 255, 255)
NAVY = (6, 12, 45)

poster_path, intro_path, clip_dir, fontdir, sfx_path, out_path = sys.argv[1:7]
previews = [float(x) for x in sys.argv[7].split(",")] if len(sys.argv) > 7 else None

SANS = f"{fontdir}/NotoSansCJKjp-Black.otf"
SANS_B = f"{fontdir}/NotoSansCJKjp-Bold.otf"
SERIF = f"{fontdir}/NotoSerifCJKjp-Black.otf"

poster = Image.open(poster_path).convert("RGBA")
PW, PH = poster.size
intro = Image.open(intro_path).convert("RGB").crop((40, 0, 1110, 668))  # 右端のスクロールバーを除く


CLIP = sorted(glob.glob(f"{clip_dir}/c_*.jpg"))


def clip_frame(i):
    """舞台映像の i コマ目を、ぼかし背景の上に大きく置く"""
    im = Image.open(CLIP[min(i, len(CLIP) - 1)]).convert("RGB")
    s_ = max(W / im.width, H / im.height) * 1.05
    small = im.resize((im.width // 4, im.height // 4))
    bg = small.resize((int(im.width * s_) + 1, int(im.height * s_) + 1), Image.BILINEAR)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = Image.eval(bg.filter(ImageFilter.GaussianBlur(40)), lambda v: int(v * 0.4)).convert("RGBA")
    fh = 1000
    fg = im.resize((int(im.width * fh / im.height), fh), Image.LANCZOS).convert("RGBA")
    return bg, fg

# ぼかした背景（ポスターが画面を覆わないときの余白用）
_s = max(W / PW, H / PH)
_bg = poster.convert("RGB").resize((int(PW * _s) + 1, int(PH * _s) + 1), Image.LANCZOS)
_bg = _bg.crop(((_bg.width - W) // 2, (_bg.height - H) // 2, (_bg.width - W) // 2 + W, (_bg.height - H) // 2 + H))
BG = Image.eval(_bg.filter(ImageFilter.GaussianBlur(40)), lambda v: int(v * 0.45)).convert("RGBA")


# ---------- 補助 ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, x):
    return a + (b - a) * x


def camera(cx, cy, s):
    """ポスター上の点 (cx, cy) を画面中央に、倍率 s で映す"""
    m = (1 / s, 0, cx - (W / 2) / s, 0, 1 / s, cy - (H / 2) / s)
    img = poster.transform((W, H), Image.AFFINE, m, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    out = BG.copy()
    out.alpha_composite(img)
    return out


def gradient(top_alpha, bottom_alpha, y0=0, y1=H):
    a = np.zeros((H, 1), np.float32)
    ys = np.arange(H)
    t = np.clip((ys - y0) / max(y1 - y0, 1), 0, 1)
    a[:, 0] = lerp(top_alpha, bottom_alpha, t)
    a = np.where((ys >= y0) & (ys <= y1), a[:, 0], 0)[:, None]
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = NAVY
    arr[..., 3] = (np.repeat(a, W, axis=1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


_font_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]


_text_cache = {}


def text(segments, path, size, stroke=None, shadow=True, tracking=0):
    """色つきの文字列を影・縁取りつきで描いた画像を返す。segments = [(文字, 色), ...]"""
    key = (tuple(segments), path, size, stroke, shadow, tracking)
    if key in _text_cache:
        return _text_cache[key]
    f = font(path, size)
    sw = stroke if stroke is not None else max(2, size // 16)
    chars = [(ch, col) for s, col in segments for ch in s]
    widths = [f.getlength(ch) + tracking for ch, _ in chars]
    tw = int(sum(widths)) + sw * 2 + 40
    th = int(size * 1.45) + sw * 2 + 40
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = 20 + sw
    for (ch, col), w in zip(chars, widths):
        d.text((x, 20 + sw), ch, font=f, fill=col, stroke_width=sw, stroke_fill=NAVY + (255,))
        x += w
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(layer.getchannel("A").point(lambda v: int(v * 0.75)))
        sh = sh.filter(ImageFilter.GaussianBlur(size // 7))
        base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        base.alpha_composite(sh, (0, size // 20))
        base.alpha_composite(layer)
        layer = base
    layer = layer.crop(layer.getbbox())
    _text_cache[key] = layer
    return layer


def place(frame, img, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0:
        return
    scale = min(scale, 1000 / img.width) if img.width * scale > 1000 else scale
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    if alpha < 1:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def pop(frame, img, cx, cy, t, t0, dur=0.18, t_out=None):
    """t0 で少し大きい状態から縮んで出る"""
    if t < t0:
        return
    k = ease_out((t - t0) / dur)
    a = k
    if t_out is not None:
        a *= 1 - clamp((t - t_out) / 0.12)
    place(frame, img, cx, cy, a, lerp(1.18, 1.0, k))


def darken(frame, amount):
    if amount <= 0:
        return frame
    ov = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(amount))))
    frame.alpha_composite(ov)
    return frame


# ---------- 文字素材 ----------
HOOK0 = text([("累計動員 ", WHITE), ("90万人", GOLD), ("突破", WHITE)], SANS, 80)
HOOK1 = text([("千と千尋の神隠し", GOLD), ("の", WHITE)], SANS, 100)
HOOK2 = text([("舞台が", WHITE), ("帰ってきた！", WHITE)], SANS, 112)

TOKYO_DATE = text([("2027.3〜5", GOLD)], SERIF, 150)
TOKYO_CITY = text([("東京", WHITE)], SANS, 210)
TOKYO_VENUE = text([("明治座", WHITE)], SANS_B, 70)

JP_HEAD = text([("愛知・大阪・福岡・北海道も", WHITE)], SANS, 78)
JP_TILES = [
    ("愛知", "2027.6", "御園座"),
    ("大阪", "2027.6〜7", "梅田芸術劇場"),
    ("福岡", "2027.7〜8", "博多座"),
    ("北海道", "2027.8", "札幌文化芸術劇場 hitaru"),
]

STAGE1 = text([("舞台版", GOLD)], SANS, 90)
STAGE2 = text([("『千と千尋の神隠し』", WHITE)], SANS, 84)

ASK1 = text([("ジブリの", WHITE), ("最新情報", GOLD), ("が", WHITE)], SANS, 100)
ASK2 = text([("知りたい方は是非", WHITE)], SANS, 100)
ASK3 = text([("フォロー", GOLD), ("お願いします", WHITE)], SANS, 100)


def tile(city, date, venue, w=440, h=300):
    t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 28, fill=(8, 16, 60, 205), outline=GOLD + (220,), width=4)
    ci = text([(city, WHITE)], SANS, 104 if len(city) <= 2 else 92, shadow=False)
    da = text([(date, GOLD)], SERIF, 60, shadow=False)
    vsize = 34 if len(venue) < 10 else 28
    ve = text([(venue, (215, 222, 245))], SANS_B, vsize, shadow=False, stroke=1)
    t.alpha_composite(da, ((w - da.width) // 2, 28))
    t.alpha_composite(ci, ((w - ci.width) // 2, 100))
    t.alpha_composite(ve, ((w - ve.width) // 2, h - ve.height - 26))
    return t


TILES = [tile(*x) for x in JP_TILES]

# 粒子（水しぶきの光）
rng = np.random.default_rng(3)
PARTICLES = [(rng.uniform(0, W), rng.uniform(300, H), rng.uniform(2, 6), rng.uniform(0, 6.28), rng.uniform(20, 70))
             for _ in range(70)]


def particles(frame, t, t0, strength):
    if strength <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for x, y, r, ph, sp in PARTICLES:
        yy = y - (t - t0) * sp
        tw = 0.5 + 0.5 * math.sin(ph + t * 5)
        a = int(255 * strength * tw)
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(210, 235, 255, a))
    glow = layer.filter(ImageFilter.GaussianBlur(6))
    frame.alpha_composite(glow)
    frame.alpha_composite(layer)


# ---------- シーン ----------
HOOK_DUR = 4.0  # 文字の場面の長さ（舞台映像を等速で 4秒）


def scene_hook(t):
    # 0.0–4.0 背景は舞台映像（座って並ぶカーテンコール、等速）。文字は画面のど真ん中に、最初のフレームから出す
    bg, fg = clip_frame(int(t * FPS))
    z = 1.0 + t * 0.012
    fw, fh = int(fg.width * z), int(fg.height * z)
    img = fg.resize((fw, fh), Image.BICUBIC)
    f = bg
    f.alpha_composite(img, (int(-(fw - W) * lerp(0.3, 0.6, ease_io(t / HOOK_DUR))), (H - fh) // 2))
    # 文字の背後（画面中央の帯）を少し暗くする。映像が透けて見える程度
    f.alpha_composite(gradient(0.0, 0.45, 590, 750))
    f.alpha_composite(gradient(0.45, 0.45, 750, 1110))
    f.alpha_composite(gradient(0.45, 0.0, 1110, 1270))
    place(f, HOOK0, W / 2, H / 2 - 190)
    # 動員数と本文の間に細い金の線
    ImageDraw.Draw(f).line((W / 2 - 180, H / 2 - 128, W / 2 + 180, H / 2 - 128), fill=GOLD + (200,), width=3)
    place(f, HOOK1, W / 2, H / 2 - 40)
    place(f, HOOK2, W / 2, H / 2 + 115)
    return f


def scene_japan(t):
    if t < 3.0:
        # 1.5–3.0 東京
        k = ease_out((t - 1.5) / 0.3)
        s = lerp(3.4, 3.0, k) + (t - 1.5) * 0.05
        f = camera(525, 290, s)
        f.alpha_composite(gradient(0.9, 0.0, 0, 330))
        f.alpha_composite(gradient(0.0, 0.92, 780, 1150))
        f.alpha_composite(gradient(0.92, 0.92, 1150, H))
        pop(f, TOKYO_DATE, W / 2, 1150, t, 1.55)
        pop(f, TOKYO_CITY, W / 2, 1345, t, 1.62)
        pop(f, TOKYO_VENUE, W / 2, 1510, t, 1.70)
        return f
    # 3.0–5.0 国内4都市
    s = 2.2 + (t - 3.0) * 0.04
    f = camera(525, 380, s)
    darken(f, 0.35)
    f.alpha_composite(gradient(0.0, 0.9, 620, 820))
    f.alpha_composite(gradient(0.9, 0.9, 820, H))
    f.alpha_composite(gradient(0.85, 0.0, 0, 420))
    pop(f, JP_HEAD, W / 2, 290, t, 3.0, 0.15)
    pos = [(300, 1010), (780, 1010), (300, 1340), (780, 1340)]
    for i, (x, y) in enumerate(pos):
        pop(f, TILES[i], x, y, t, 3.05 + i * 0.25, 0.16)
    return f


def scene_intro(t):
    # 5.0–9.5 introduction 画像を1行ずつ
    lt = t - 5.0
    z = 1.0 + lt * 0.006
    iw = int(W * z)
    ih = int(intro.height * iw / intro.width)
    img = intro.resize((iw, ih), Image.LANCZOS)
    arr = np.asarray(img).astype(np.float32)
    ys = np.arange(ih) / ih * 668  # 元画像の y
    alpha = np.zeros(ih, np.float32)
    rows = [(60, 180, 0.0, 0.35), (300, 400, 0.6, 0.2), (405, 505, 1.6, 0.2), (510, 610, 2.6, 0.2)]
    for y0, y1, st, du in rows:
        inside = (ys >= y0) & (ys < y1)
        a = clamp((lt - st) / du)
        alpha[inside] = a
    arr *= alpha[:, None, None]
    img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # 最後の行でわずかに揺らす（「ドン」に合わせる）
    shake = 0
    if 2.6 <= lt < 2.9:
        shake = int(10 * math.sin((lt - 2.6) * 60) * (1 - (lt - 2.6) / 0.3))
    f.alpha_composite(img, ((W - iw) // 2, 880 - ih // 2 + shake))
    return f


def scene_poster(t):
    # 9.5–14.0 ポスター：日程とハクが見える画から、千尋へゆっくり寄っていく（次の場面の最初の画につながる）
    k = ease_io((t - 9.5) / 4.5)
    f = camera(lerp(528, 610, k), lerp(540, 650, k), lerp(1.8, 2.4, k))
    particles(f, t, 9.5, 0.6)
    return f


def scene_full(t):
    # 14.0–18.0 ポスター全体へ引く
    k = ease_io((t - 14.0) / 3.2)
    s = lerp(2.4, 1.2, k)
    cx = lerp(610, 528, k)
    cy = lerp(650, 790, k)
    f = camera(cx, cy, s)
    particles(f, t, 14.0, clamp((t - 14.0) / 0.4) * 0.9)
    a = ease_out((t - 15.4) / 0.4)
    if a > 0:
        f.alpha_composite(gradient(0.93 * a, 0.93 * a, 0, 480))
        f.alpha_composite(gradient(0.93 * a, 0.0, 480, 760))
    pop(f, STAGE1, W / 2, 260, t, 15.4, 0.25)
    pop(f, STAGE2, W / 2, 390, t, 15.55, 0.25)
    return f


def scene_ask(t):
    # 18.0–21.0 問いかけ → 暗転
    f = camera(528, 790, 1.2 + (t - 18.0) * 0.015)
    particles(f, t, 14.0, 0.9)
    darken(f, 0.55 * ease_out((t - 18.0) / 0.3))
    pop(f, ASK1, W / 2, H / 2 - 150, t, 18.05, 0.2)
    pop(f, ASK2, W / 2, H / 2, t, 18.15, 0.2)
    pop(f, ASK3, W / 2, H / 2 + 150, t, 18.3, 0.2)
    darken(f, ease_io((t - 19.9) / 0.5))
    return f


def frame_at(t):
    if t < HOOK_DUR:
        return scene_hook(t)
    t = t - HOOK_DUR + 1.5  # 以降の場面は、もとの作り（文字の場面 1.5秒）の時間で動く
    if t < 5.0:
        return scene_japan(t)
    if t < 9.5:
        return scene_intro(t)
    if t < 14.0:
        return scene_poster(t)
    if t < 18.0:
        return scene_full(t)
    return scene_ask(t)


if previews:
    for p in previews:
        frame_at(p).convert("RGB").save(f"{out_path}_{p:05.2f}.jpg", quality=88)
    sys.exit()

ff = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [ff, "-y", "-loglevel", "error",
       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", sfx_path,
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = int((21.0 - 1.5 + HOOK_DUR) * FPS)
for i in range(n):
    proc.stdin.write(frame_at(i / FPS).convert("RGB").tobytes())
    if i % 60 == 0:
        print(f"{i}/{n}", flush=True)
proc.stdin.close()
proc.wait()
