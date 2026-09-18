"""ノート落書き風フレームの描画 (Pillow + numpy)。

紙 = ルーズリーフ。線 = 手描きの鉛筆。色は強調の2色だけ。
1ステップごとにジッタの乱数を引き直すので、線が小刻みに揺れて
パラパラ漫画っぽく見える。
"""

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- 画面 -------------------------------------------------------------------
W, H = 1080, 1920

# --- 紙 ---------------------------------------------------------------------
PAPER = (250, 246, 234)
RULE = (152, 180, 216)          # 青い罫線
MARGIN_RED = (214, 122, 118)    # 左の赤い縦線
RULE_TOP = 210                  # 一番上の罫線
RULE_GAP = 78                   # 罫線の間隔
MARGIN_X = 150                  # 赤い縦線の位置
TEXT_X = 190                    # 書き始め

# --- 筆記具 -----------------------------------------------------------------
INK = (42, 44, 52)              # 鉛筆
RED_PENCIL = (204, 62, 54)      # 赤の色鉛筆 (強調その1)
MARKER = (255, 214, 72)         # 黄色マーカー (強調その2)

# --- キャラの骨格 -----------------------------------------------------------
CX = W // 2
HEAD_CY, HEAD_RX, HEAD_RY = 690, 96, 103
SH_Y, HIP_Y = 830, 1020
SH_HALF, HIP_HALF = 46, 58
UPPER_ARM, FOREARM = 112, 104
THIGH, SHIN = 130, 136
FOOT_Y = HIP_Y + THIGH + SHIN


# --- フォント ---------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CANDIDATES = [
    (os.path.join(_HERE, "fonts", "ZenKurenaido-Regular.ttf"), None),
    (os.path.join(_HERE, "fonts", "Yomogi-Regular.ttf"), None),
    (os.path.join(_HERE, "fonts", "KleeOne-SemiBold.ttf"), None),
    ("/usr/share/fonts/truetype/motoya/MTLc3m.ttf", None),          # 丸ゴシック
    ("/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", None),
    ("C:/Windows/Fonts/HGRSMP.TTF", None),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "JP"),
]


def _resolve_font_path():
    for path, want in FONT_CANDIDATES:
        if os.path.exists(path):
            return path, want
    raise RuntimeError("日本語フォントが見つかりません (fetch_fonts.sh を実行してください)")


_FONT_PATH, _FONT_WANT = _resolve_font_path()
_font_cache = {}


def font(size):
    if size in _font_cache:
        return _font_cache[size]
    idx = 0
    if _FONT_WANT:
        for i in range(12):
            try:
                f = ImageFont.truetype(_FONT_PATH, size, index=i)
            except Exception:
                break
            if _FONT_WANT in " ".join(f.getname()):
                idx = i
                break
    f = ImageFont.truetype(_FONT_PATH, size, index=idx)
    _font_cache[size] = f
    return f


def rule_y(k):
    """k本目の罫線のy座標 (文字のベースラインに使う)。"""
    return RULE_TOP + k * RULE_GAP


# --- 紙の生成 (静的なので1回だけ) -------------------------------------------
def make_background():
    rnd = np.random.default_rng(4)

    base = np.empty((H, W, 3), dtype=np.float32)
    base[:] = np.array(PAPER, dtype=np.float32)

    # 紙の皺 (低周波のムラ)
    small = rnd.normal(0.0, 1.0, (30, 18)).astype(np.float32)
    wrinkle = np.array(Image.fromarray(small, "F").resize((W, H), Image.BICUBIC))
    base += wrinkle[..., None] * 1.7

    # 紙の繊維 (高周波のノイズ)
    grain = rnd.normal(0.0, 2.0, (H, W)).astype(np.float32)
    base += grain[..., None]

    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")

    # 青い罫線
    k = 0
    while rule_y(k) < H - 60:
        y = rule_y(k)
        d.line([(60, y), (W - 50, y)], fill=(*RULE, 120), width=2)
        k += 1

    # 左の赤い縦線
    d.line([(MARGIN_X, 0), (MARGIN_X, H)], fill=(*MARGIN_RED, 150), width=3)

    # 綴じ穴
    for hy in (330, H // 2, H - 330):
        d.ellipse([58, hy - 26, 110, hy + 26], fill=(238, 233, 220),
                  outline=(214, 208, 194), width=2)

    return img


# --- 手描きの線 -------------------------------------------------------------
def _rough(p0, p1, rng, amp=2.0, seg=None):
    """2点の間を、少し震えた折れ線にする。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1.0
    if seg is None:
        seg = max(2, int(length / 42))
    nx, ny = -dy / length, dx / length
    pts = []
    for i in range(seg + 1):
        u = i / seg
        k = math.sin(math.pi * u)                    # 中央ほど大きく震える
        off = rng.uniform(-amp, amp) * (0.3 + 0.7 * k)
        pts.append((p0[0] + dx * u + nx * off, p0[1] + dy * u + ny * off))
    return pts


def _stroke(d, pts, rng, w, color, alpha):
    """折れ線を、太さを揺らしながら引く。"""
    col = (*color, alpha)
    for i in range(len(pts) - 1):
        ww = max(2.0, w + rng.uniform(-1.1, 1.1))
        d.line([pts[i], pts[i + 1]], fill=col, width=int(round(ww)))
        r = ww / 2.0
        for p in (pts[i], pts[i + 1]):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def sketch_line(d, p0, p1, rng, w=7, color=INK, passes=2, over=4.0):
    """定規を使っていない線。始点・終点は少しはみ出す。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    for p in range(passes):
        o0, o1 = rng.uniform(0, over), rng.uniform(0, over)
        a = (p0[0] - ux * o0, p0[1] - uy * o0)
        b = (p1[0] + ux * o1, p1[1] + uy * o1)
        _stroke(d, _rough(a, b, rng, amp=1.5 + 0.7 * p), rng,
                w - p * 1.2, color, 228 if p == 0 else 118)


def sketch_path(d, pts, rng, w=7, color=INK, passes=2, closed=False, over=2.0):
    seq = list(pts) + ([pts[0]] if closed else [])
    for i in range(len(seq) - 1):
        sketch_line(d, seq[i], seq[i + 1], rng, w=w, color=color,
                    passes=passes, over=over)


def sketch_ellipse(d, cx, cy, rx, ry, rng, w=7, color=INK, passes=2,
                   a0=0.0, a1=2 * math.pi):
    """手で描いた丸 (少し歪む・描き始めと終わりが重なる)。"""
    for p in range(passes):
        span = a1 - a0
        n = max(8, int(abs(span) * max(rx, ry) / 17))
        ph = rng.uniform(0, 6.28)
        wob = rng.uniform(0.02, 0.055)
        start = a0 - rng.uniform(0.0, 0.12)
        end = a1 + rng.uniform(0.0, 0.18)
        pts = []
        for i in range(n + 1):
            a = start + (end - start) * i / n
            k = 1 + wob * math.sin(3 * a + ph) + rng.uniform(-0.012, 0.012)
            pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
        _stroke(d, pts, rng, w - p * 1.2, color, 228 if p == 0 else 112)


def marker_fill(d, box, rng, color=MARKER, alpha=115):
    """マーカーで雑に塗った風の帯。"""
    x0, y0, x1, y1 = box
    n = max(2, int((y1 - y0) / 22))
    for i in range(n):
        yy = y0 + (y1 - y0) * (i + 0.5) / n
        a = (x0 - rng.uniform(2, 16), yy + rng.uniform(-7, 7))
        b = (x1 + rng.uniform(2, 18), yy + rng.uniform(-7, 7))
        d.line([a, b], fill=(*color, alpha), width=int((y1 - y0) / n) + 8)


# --- 手書きテキスト ---------------------------------------------------------
def hand_text(img, xy, text, f, fill=INK, angle=0.0, anchor="ls", alpha=240):
    """わずかに傾けて書いた風のテキスト (xy はベースライン左端)。"""
    pad = 40
    tmp = Image.new("RGBA", (W + pad * 2, int(f.size * 2.6) + pad * 2), (0, 0, 0, 0))
    ox, oy = pad, pad + f.size
    ImageDraw.Draw(tmp).text((ox, oy), text, font=f, fill=(*fill, alpha), anchor=anchor)
    if abs(angle) > 0.01:
        tmp = tmp.rotate(angle, resample=Image.BICUBIC, center=(ox, oy))
    img.paste(tmp, (int(xy[0] - ox), int(xy[1] - oy)), tmp)


def text_span(text, word, f):
    """text の中の word の (開始x, 幅)。見つからなければ None。"""
    i = text.find(word)
    if i < 0:
        return None
    return f.getlength(text[:i]), f.getlength(word)


# --- キャラ -----------------------------------------------------------------
def _tip(origin, deg, length, side):
    a = math.radians(deg)
    return (origin[0] + side * math.sin(a) * length,
            origin[1] + math.cos(a) * length)


def blink_schedule(duration, seed=7):
    rnd = random.Random(seed)
    times, t = [], 1.4
    while t < duration:
        times.append(t)
        t += rnd.uniform(2.0, 3.8)
    return times


def _blinking(t, schedule, dur=0.18):
    return any(bt <= t < bt + dur for bt in schedule)


def draw_character(d, t, mouth, speak, blinks, rng):
    bob = math.sin(2 * math.pi * 0.75 * t) * 8.0 * (0.45 + 0.55 * speak)
    sway = math.sin(2 * math.pi * 0.33 * t) * 6.0
    dx, dy = sway, bob

    sh = (CX + dx, SH_Y + dy)
    hip = (CX + dx, HIP_Y + dy)
    hcx, hcy = CX + dx + sway * 0.3, HEAD_CY + dy * 1.12

    # 胴 (棒より少しだけ肉付け)
    for side in (-1, 1):
        sketch_path(d, [(sh[0] + side * SH_HALF, sh[1]),
                        (sh[0] + side * (SH_HALF + 6), sh[1] + 96),
                        (hip[0] + side * HIP_HALF, hip[1])], rng, w=7)
    sketch_line(d, (sh[0] - SH_HALF, sh[1]), (sh[0] + SH_HALF, sh[1]), rng, w=7)
    sketch_line(d, (hip[0] - HIP_HALF + 6, hip[1]), (hip[0] + HIP_HALF - 6, hip[1]),
                rng, w=7)

    # 脚
    for side in (-1, 1):
        h = (hip[0] + side * (HIP_HALF - 6), hip[1])
        knee = _tip(h, side * 6, THIGH, 1)
        foot = _tip(knee, side * 2, SHIN, 1)
        sketch_line(d, h, knee, rng, w=7)
        sketch_line(d, knee, (foot[0], FOOT_Y + dy * 0.2), rng, w=7)
        sketch_line(d, (foot[0] - 4, FOOT_Y + dy * 0.2),
                    (foot[0] + side * 34, FOOT_Y + dy * 0.2 - 4), rng, w=7)

    # 腕
    wob = 2 * math.pi * 1.05 * t
    arms = [
        (-1, 24 + 7 * math.sin(wob * 0.6 + 1.3) + 16 * speak * math.sin(wob + 2.1),
             26 + 10 * math.sin(wob * 0.8 + 2.0) + 30 * speak * math.sin(wob + 1.4)),
        (1, 28 + 6 * math.sin(wob * 0.7) + 22 * speak * math.sin(wob),
            30 + 9 * math.sin(wob * 0.9 + 0.5) + 34 * speak * math.sin(wob + 0.9)),
    ]
    for side, a_up, a_fore in arms:
        a_up += rng.uniform(-3.0, 3.0)
        a_fore += rng.uniform(-3.5, 3.5)
        s = (sh[0] + side * (SH_HALF - 8), sh[1] + 10)
        elbow = _tip(s, a_up, UPPER_ARM, side)
        hand = _tip(elbow, a_up + a_fore, FOREARM, side)
        sketch_line(d, s, elbow, rng, w=7)
        sketch_line(d, elbow, hand, rng, w=7)
        sketch_ellipse(d, hand[0], hand[1], 15, 14, rng, w=5, passes=1)

    # 首
    sketch_line(d, (hcx, hcy + HEAD_RY - 6), (sh[0], sh[1] + 2), rng, w=6, over=2)

    # 頭
    sketch_ellipse(d, hcx, hcy, HEAD_RX, HEAD_RY, rng, w=7)

    # 二角帽 (ナポレオンらしさはこれだけ)
    hy = hcy - HEAD_RY + 12
    sketch_path(d, [
        (hcx - 134, hy - 4), (hcx - 56, hy - 56), (hcx, hy - 64),
        (hcx + 56, hy - 56), (hcx + 134, hy - 4), (hcx + 64, hy + 18),
        (hcx - 64, hy + 18),
    ], rng, w=7, closed=True)

    # 顔
    blink = _blinking(t, blinks)
    for side in (-1, 1):
        ex, ey = hcx + side * 31, hcy - 10
        if blink:
            sketch_line(d, (ex - 16, ey), (ex + 16, ey), rng, w=6, passes=1, over=2)
        else:
            d.ellipse([ex - 9, ey - 11, ex + 9, ey + 11], fill=(*INK, 235))

    if mouth < 0.18:                                  # 閉じ口
        sketch_line(d, (hcx - 22, hcy + 50), (hcx + 22, hcy + 48), rng,
                    w=6, passes=1, over=2)
    else:                                             # 開き口
        mh = 10 + 38 * mouth
        sketch_ellipse(d, hcx, hcy + 52, 24 + 9 * mouth, mh / 2, rng, w=5, passes=1)


# --- 書き足した風の装飾 -----------------------------------------------------
def draw_focus_lines(d, rng, reveal, cx, cy):
    """集中線。reveal で本数が増える。"""
    total = 18
    for i in range(int(total * reveal)):
        a = 2 * math.pi * i / total + 0.16
        r0 = 285 + rng.uniform(-16, 16)
        r1 = r0 + rng.uniform(75, 140)
        sketch_line(d, (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                    (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
                    rng, w=5, passes=1, over=3)


def draw_mark(d, kind, box, rng, reveal):
    """字幕の語に重ねる強調。box は (x0, y0, x1, y1)。"""
    x0, y0, x1, y1 = box
    if reveal <= 0.02:
        return
    if kind == "marker":
        marker_fill(d, (x0, y0, x0 + (x1 - x0) * reveal, y1), rng)
    elif kind == "circle":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        sketch_ellipse(d, cx, cy, (x1 - x0) / 2 + 22, (y1 - y0) / 2 + 16, rng,
                       w=6, color=RED_PENCIL, passes=1,
                       a0=-2.4, a1=-2.4 + 2 * math.pi * reveal)
        if reveal > 0.85:
            sketch_ellipse(d, cx, cy, (x1 - x0) / 2 + 28, (y1 - y0) / 2 + 22, rng,
                           w=5, color=RED_PENCIL, passes=1, a0=-2.1, a1=2.6)
    elif kind == "underline":
        xe = x0 + (x1 - x0) * reveal
        sketch_line(d, (x0, y1 + 8), (xe, y1 + 8), rng, w=6,
                    color=RED_PENCIL, passes=1)
        if reveal > 0.6:
            sketch_line(d, (x0, y1 + 22), (x0 + (x1 - x0) * (reveal - 0.6) / 0.4,
                        y1 + 22), rng, w=5, color=RED_PENCIL, passes=1)


def draw_arrow(d, p0, p1, rng, color=INK, reveal=1.0):
    ex = (p0[0] + (p1[0] - p0[0]) * reveal, p0[1] + (p1[1] - p0[1]) * reveal)
    sketch_line(d, p0, ex, rng, w=6, color=color, passes=1)
    if reveal > 0.7:
        a = math.atan2(ex[1] - p0[1], ex[0] - p0[0])
        for s in (-1, 1):
            b = a + math.pi + s * 0.45
            sketch_line(d, ex, (ex[0] + math.cos(b) * 34, ex[1] + math.sin(b) * 34),
                        rng, w=6, color=color, passes=1)


# --- 画面の組み立て ---------------------------------------------------------
def draw_title(img, d, title_lines, rng, marker_word=None):
    f = font(80)
    for i, line in enumerate(title_lines):
        y = rule_y(1 + i)
        if marker_word and marker_word in line:
            span = text_span(line, marker_word, f)
            if span:
                marker_fill(d, (TEXT_X + span[0] - 6, y - 62,
                                TEXT_X + span[0] + span[1] + 6, y + 10), rng)
        hand_text(img, (TEXT_X, y), line, f, INK, angle=-0.6 + 0.4 * i)


def draw_tag(img, d, text, rng):
    hand_text(img, (TEXT_X, rule_y(0)), text, font(36), (96, 108, 140), angle=-0.5)


def draw_subtitle(img, d, lines, mark, rng, reveal):
    f = font(58)
    for i, line in enumerate(lines):
        y = rule_y(15 + i)
        hand_text(img, (TEXT_X, y), line, f, INK, angle=(-0.5 if i == 0 else 0.4))
        if mark and mark.get("line") == i:
            span = text_span(line, mark["word"], f)
            if span:
                box = (TEXT_X + span[0], y - 56, TEXT_X + span[0] + span[1], y + 8)
                draw_mark(d, mark["kind"], box, rng, reveal)


def draw_progress(d, p, rng):
    y = H - 74
    sketch_line(d, (TEXT_X, y), (TEXT_X + (W - TEXT_X - 150) * max(p, 0.004), y),
                rng, w=6, passes=1, over=2)


def draw_frame(bg, t, duration, title_lines, tag, subtitle, mark, reveal,
               mouth, speak, blinks, step):
    """1ステップ分の絵。step ごとに乱数を引き直すので線が揺れる。"""
    rng = random.Random(1000 + step)
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")

    draw_tag(img, d, tag, rng)
    draw_title(img, d, title_lines, rng, marker_word="チビじゃなかった")
    if mark and mark.get("kind") == "focus":
        draw_focus_lines(d, rng, reveal, CX, HEAD_CY + 170)
    draw_character(d, t, mouth, speak, blinks, rng)
    draw_subtitle(img, d, subtitle, mark, rng, reveal)
    draw_progress(d, min(1.0, t / duration), rng)
    return img
