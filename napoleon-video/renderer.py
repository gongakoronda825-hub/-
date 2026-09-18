"""棒人間フレームの描画 (Pillow + numpy)。"""

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- 画面設定 ---------------------------------------------------------------
W, H = 1080, 1920

BG_TOP = (28, 38, 74)
BG_BOTTOM = (10, 13, 28)
GLOW = (70, 95, 165)

INK = (240, 244, 255)          # 棒人間の線
ACCENT = (255, 205, 90)        # タイトル下線・強調
SUB_BG = (8, 10, 20)
SUB_FG = (255, 255, 255)

# --- 棒人間の骨格 (静止時の基準座標) ----------------------------------------
CX = W // 2
GROUND_Y = 1370
HIP_Y = GROUND_Y - 320
SH_Y = HIP_Y - 235
HEAD_R = 88
HEAD_CY = SH_Y - 136
LIMB_W = 16

UPPER_ARM, FOREARM = 118, 112
THIGH, SHIN = 148, 156


# --- フォント ---------------------------------------------------------------
FONT_CANDIDATES = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "JP"),
    ("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", None),
    ("C:/Windows/Fonts/meiryob.ttc", None),
    ("C:/Windows/Fonts/YuGothB.ttc", None),
]


def _resolve_font_path():
    for path, want in FONT_CANDIDATES:
        if os.path.exists(path):
            return path, want
    raise RuntimeError("日本語フォントが見つかりません")


_FONT_PATH, _FONT_WANT = _resolve_font_path()
_font_cache = {}


def font(size):
    """サイズ指定で日本語フォントを返す (.ttc は JP フェイスを探す)。"""
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


# --- 背景 (静的なので1回だけ作って使い回す) ---------------------------------
def make_background():
    y = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    top = np.array(BG_TOP, dtype=np.float32)
    bottom = np.array(BG_BOTTOM, dtype=np.float32)
    grad = top[None, None, :] * (1 - y[..., None]) + bottom[None, None, :] * y[..., None]
    grad = np.repeat(grad, W, axis=1)

    # 棒人間の後ろにやわらかい光
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - CX) / 520.0) ** 2 + ((yy - (SH_Y + 60)) / 620.0) ** 2)
    halo = np.clip(1.0 - d, 0.0, 1.0) ** 2
    grad += np.array(GLOW, dtype=np.float32)[None, None, :] * halo[..., None] * 0.55

    img = Image.fromarray(np.clip(grad, 0, 255).astype(np.uint8), "RGB")

    d = ImageDraw.Draw(img, "RGBA")
    # 地面のライン
    d.line([(120, GROUND_Y + 34), (W - 120, GROUND_Y + 34)], fill=(255, 255, 255, 38), width=3)
    return img


# --- 描画ヘルパ -------------------------------------------------------------
def _limb(d, p0, p1, width=LIMB_W, color=INK):
    d.line([p0, p1], fill=color, width=width)
    r = width / 2.0
    for p in (p0, p1):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def _tip(origin, deg, length, side):
    """origin から「真下を0度」として side 方向に deg 傾けた先端座標。"""
    a = math.radians(deg)
    return (origin[0] + side * math.sin(a) * length,
            origin[1] + math.cos(a) * length)


# --- まばたきのスケジュール -------------------------------------------------
def blink_schedule(duration, seed=7):
    rnd = random.Random(seed)
    times, t = [], 1.2
    while t < duration:
        times.append(t)
        t += rnd.uniform(2.2, 4.0)
    return times


def _blink_amount(t, schedule, dur=0.13):
    for bt in schedule:
        if bt <= t < bt + dur:
            return math.sin(math.pi * (t - bt) / dur)
    return 0.0


# --- 棒人間 -----------------------------------------------------------------
def draw_stickman(d, t, mouth, speak, blinks):
    """t: 経過秒 / mouth: 口の開き0-1 / speak: 話している度合い0-1"""
    bob = math.sin(2 * math.pi * 0.8 * t) * 9.0 * (0.5 + 0.5 * speak)
    sway = math.sin(2 * math.pi * 0.37 * t) * 7.0
    dx, dy = sway, bob

    hip = (CX + dx, HIP_Y + dy)
    sh = (CX + dx, SH_Y + dy)
    head_c = (CX + dx + sway * 0.25, HEAD_CY + dy * 1.15)

    # 影
    sr = 96
    d.ellipse([CX + dx * 0.4 - sr, GROUND_Y + 18, CX + dx * 0.4 + sr, GROUND_Y + 50],
              fill=(0, 0, 0, 90))

    # 脚
    for side in (-1, 1):
        h = (hip[0] + side * 34, hip[1])
        knee = _tip(h, side * 7, THIGH, 1)
        foot = _tip(knee, side * 3, SHIN, 1)
        _limb(d, h, knee)
        _limb(d, knee, (foot[0], GROUND_Y + dy * 0.15))

    # 胴
    _limb(d, hip, sh, width=LIMB_W + 3)

    # 腕 (話している時ほど大きくジェスチャー)
    wob = 2 * math.pi * 1.15 * t
    arms = [
        (-1, 22 + 7 * math.sin(wob * 0.6 + 1.3) + 8 * speak * math.sin(wob + 2.1),
             28 + 12 * math.sin(wob * 0.8 + 2.0) + 30 * speak * math.sin(wob + 1.4)),
        (1, 26 + 6 * math.sin(wob * 0.7) + 20 * speak * math.sin(wob),
            30 + 10 * math.sin(wob * 0.9 + 0.5) + 36 * speak * math.sin(wob + 0.9)),
    ]
    for side, a_up, a_fore in arms:
        s = (sh[0] + side * 12, sh[1] + 14)
        elbow = _tip(s, a_up, UPPER_ARM, side)
        hand = _tip(elbow, a_up + a_fore, FOREARM, side)
        _limb(d, s, elbow)
        _limb(d, elbow, hand)
        d.ellipse([hand[0] - 13, hand[1] - 13, hand[0] + 13, hand[1] + 13], fill=INK)

    # 首
    _limb(d, (sh[0], sh[1] - 2), (head_c[0], head_c[1] + HEAD_R - 4), width=LIMB_W - 2)

    # 頭
    hx, hy = head_c
    d.ellipse([hx - HEAD_R, hy - HEAD_R, hx + HEAD_R, hy + HEAD_R],
              fill=(18, 24, 46), outline=INK, width=LIMB_W)

    # 目 (まばたき)
    blink = _blink_amount(t, blinks)
    eye_r = 12
    open_h = eye_r * (1.0 - blink)
    for side in (-1, 1):
        ex = hx + side * 33
        ey = hy - 16
        if open_h < 3:
            d.line([(ex - eye_r, ey), (ex + eye_r, ey)], fill=INK, width=6)
        else:
            d.ellipse([ex - eye_r, ey - open_h, ex + eye_r, ey + open_h], fill=INK)

    # 眉 (少しだけ表情)
    for side in (-1, 1):
        ex = hx + side * 33
        d.line([(ex - 17, hy - 48 + side * 3), (ex + 17, hy - 51 - side * 3)],
               fill=INK, width=6)

    # 口パク
    mw = 26 + 15 * mouth
    mh = 5 + 30 * mouth
    d.ellipse([hx - mw, hy + 30 - mh / 2, hx + mw, hy + 30 + mh / 2],
              fill=INK if mouth < 0.15 else (255, 150, 150),
              outline=INK, width=5)


# --- テキスト ---------------------------------------------------------------
def _text_center(d, cx, y, text, f, fill, stroke=0, stroke_fill=(0, 0, 0)):
    d.text((cx, y), text, font=f, fill=fill, anchor="ma",
           stroke_width=stroke, stroke_fill=stroke_fill)


def draw_title(d, title, t):
    f = font(84)
    lines = title.split("\n")
    y = 150
    d.rounded_rectangle([CX - 120, y - 76, CX + 120, y - 14], radius=28, fill=ACCENT)
    _text_center(d, CX, y - 70, "歴史の雑学", font(40), (25, 25, 35))
    for line in lines:
        _text_center(d, CX, y, line, f, (255, 255, 255), stroke=6, stroke_fill=(12, 16, 32))
        y += 104
    bar = 150 + 40 * math.sin(2 * math.pi * 0.25 * t)
    d.rounded_rectangle([CX - bar, y + 14, CX + bar, y + 24], radius=6, fill=ACCENT)


def draw_subtitle(d, text, reveal=1.0):
    if not text:
        return
    lines = text.split("\n")
    f = font(64)
    line_h = 88
    pad = 36
    top = 1520
    box_h = line_h * len(lines) + pad * 2 - 20
    d.rounded_rectangle([70, top, W - 70, top + box_h], radius=32, fill=(*SUB_BG, 205))
    d.rounded_rectangle([70, top, 82, top + box_h], radius=6, fill=ACCENT)
    y = top + pad - 6
    for line in lines:
        _text_center(d, CX, y, line, f, SUB_FG, stroke=4, stroke_fill=(0, 0, 0))
        y += line_h


def draw_progress(d, p):
    d.rectangle([0, H - 12, W, H], fill=(255, 255, 255, 40))
    d.rectangle([0, H - 12, int(W * p), H], fill=ACCENT)


# --- 1フレーム --------------------------------------------------------------
def draw_frame(bg, t, duration, title, subtitle, mouth, speak, blinks):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    draw_title(d, title, t)
    draw_stickman(d, t, mouth, speak, blinks)
    draw_subtitle(d, subtitle)
    draw_progress(d, min(1.0, t / duration))
    return img
