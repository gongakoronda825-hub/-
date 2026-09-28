"""舞台『千と千尋の神隠し』TikTok動画（1080x1920 / 30fps / 21秒）を書き出す。

使い方: python3 render.py <poster.jpg> <intro.jpg> <fontdir> <sfx.wav> <out.mp4> [preview秒,...]
"""
import math
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 21.0
GOLD = (236, 200, 120)
WHITE = (255, 255, 255)
NAVY = (6, 12, 45)

poster_path, intro_path, fontdir, sfx_path, out_path = sys.argv[1:6]
previews = [float(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None

SANS = f"{fontdir}/NotoSansCJKjp-Black.otf"
SANS_B = f"{fontdir}/NotoSansCJKjp-Bold.otf"
SERIF = f"{fontdir}/NotoSerifCJKjp-Black.otf"

poster = Image.open(poster_path).convert("RGBA")
PW, PH = poster.size
intro = Image.open(intro_path).convert("RGB").crop((40, 0, 1110, 668))  # 右端のスクロールバーを除く

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
HOOK1 = text([("ジブリ", GOLD), ("『千と千尋』の", WHITE)], SANS, 90)
HOOK2 = text([("舞台、", WHITE), ("日本で", GOLD), ("やります", WHITE)], SANS, 96)

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

WORLD_HEAD = text([("そして、", WHITE), ("世界へ", GOLD)], SANS, 100)
WORLD = [
    # (ポスター上の位置, 日付, 都市, 劇場)
    ((170, 205), "2026.12〜2027.1", "台北", "国家戯劇院"),
    ((880, 210), "2027.5〜8", "トロント", "Princess of Wales Theatre"),
    ((170, 345), "2027.9〜10", "ロサンゼルス", "Ahmanson Theatre"),
    ((880, 345), "2028.3〜7", "ロンドン", "London Coliseum"),
]

STAGE1 = text([("舞台版", GOLD)], SANS, 90)
STAGE2 = text([("『千と千尋の神隠し』", WHITE)], SANS, 84)

ASK1 = text([("あなたは", WHITE)], SANS, 130)
ASK2 = text([("どこで", GOLD), ("観る？", WHITE)], SANS, 150)
ASK3 = text([("コメントで教えてね", WHITE)], SANS_B, 58)


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


def shine(frame, t, t0, dur, y0, y1):
    """金文字に光が走る"""
    k = (t - t0) / dur
    if not 0 <= k <= 1:
        return frame
    arr = np.asarray(frame).astype(np.float32)
    region = arr[y0:y1, :, :3]
    lum = region.mean(axis=2)
    mask = np.clip((lum - 120) / 100, 0, 1)
    xs = np.arange(W)[None, :]
    ys = np.arange(y1 - y0)[:, None]
    pos = lerp(-300, W + 300, ease_io(k))
    band = np.exp(-(((xs + ys * 0.6) - pos) / 70) ** 2)
    region += (band * mask * 190)[..., None]
    arr[y0:y1, :, :3] = np.clip(region, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ---------- シーン ----------
def scene_hook(t):
    # 0.0–1.5 最初のフレームから答えを見せる（フェードなし）
    s = lerp(1.30, 1.36, t / 1.5)
    f = camera(528, 800, s)
    f.alpha_composite(gradient(0.92, 0.0, 0, 900))
    place(f, HOOK1, W / 2, 330)
    place(f, HOOK2, W / 2, 480)
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


def scene_world(t):
    if t < 10.6:
        # 9.5–10.6 WORLD TOUR 2026-2028
        k = ease_out((t - 9.5) / 1.1)
        s = lerp(1.02, 1.08, k)
        f = camera(528, lerp(420, 400, k), s)
        y = int(H / 2 + (70 - lerp(420, 400, k)) * s)
        return shine(f, t, 9.6, 0.8, max(0, y - 70), y + 70)
    # 10.6–14.0 海外4都市
    i = min(3, int((t - 10.6) / 0.85))
    t0 = 10.6 + i * 0.85
    (cx, cy), date, city, venue = WORLD[i]
    k = ease_out((t - t0) / 0.25)
    s = lerp(3.3, 2.8, k) + (t - t0) * 0.08
    f = camera(cx, cy + 45, s)
    f.alpha_composite(gradient(0.95, 0.95, 0, 380))
    f.alpha_composite(gradient(0.95, 0.0, 380, 520))
    f.alpha_composite(gradient(0.0, 0.95, 700, 960))
    f.alpha_composite(gradient(0.95, 0.95, 960, H))
    place(f, WORLD_HEAD, W / 2, 270, ease_out((t - 10.6) / 0.15))
    d = text([(date, GOLD)], SERIF, 96 if len(date) < 12 else 80)
    c = text([(city, WHITE)], SANS, 170 if len(city) <= 4 else 140)
    v = text([(venue, WHITE)], SANS_B, 56)
    pop(f, d, W / 2, 1160, t, t0 + 0.03)
    pop(f, c, W / 2, 1340, t, t0 + 0.08)
    pop(f, v, W / 2, 1500, t, t0 + 0.12)
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
    pop(f, ASK1, W / 2, 800, t, 18.05, 0.2)
    pop(f, ASK2, W / 2, 980, t, 18.15, 0.2)
    pop(f, ASK3, W / 2, 1170, t, 18.5, 0.2)
    darken(f, ease_io((t - 19.9) / 0.5))
    return f


def frame_at(t):
    if t < 1.5:
        return scene_hook(t)
    if t < 5.0:
        return scene_japan(t)
    if t < 9.5:
        return scene_intro(t)
    if t < 14.0:
        return scene_world(t)
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
n = int(DUR * FPS)
for i in range(n):
    proc.stdin.write(frame_at(i / FPS).convert("RGB").tobytes())
    if i % 60 == 0:
        print(f"{i}/{n}", flush=True)
proc.stdin.close()
proc.wait()
