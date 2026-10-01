"""画像・ナレーション・効果音・テロップを合わせて 1080x1920 の mp4 を書き出す。

フレームはすべて PIL で描いて ffmpeg にパイプする（テロップ・字幕も PIL で描くので、縁取りや影、
アニメーションを細かく作り込める）。
"""
import json
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from script import CTA_TEXT, SCENES

B = "build"
OUT = sys.argv[1] if len(sys.argv) > 1 else "mimi_imax_tiktok.mp4"
W, H, FPS = 1080, 1920, 30
LEAD, TAIL, LAST_TAIL = 0.08, 0.14, 0.7  # 各シーンの前後の間（秒）
XFADE = 0.16  # 画像の切り替えのクロスフェード（秒）
LAST_XFADE = 0.6  # 締めのシーンへの切り替え

# レイアウト（TikTok の UI がかぶる上端 ~150px・下端 ~350px・右端の操作ボタンを避ける）
CARD_W, CARD_H, CARD_Y, CARD_R = 1080, 1000, 580, 34  # 横長の写真は横幅いっぱい・縦1000pxで大きく見せる
TELOP_TOP = 205
SUB_CY = 1468  # 字幕ブロックの中心（写真の下部に重ねる）
POSTER_H, POSTER_SUB_CY = 890, 1545  # 縦長ポスターは少し低めにして、字幕はロゴにかぶらないよう下に出す
SUB_MAX_W = 900

YELLOW = (255, 226, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
F_TELOP = "fonts/MPLUSRounded1c-Black.ttf"
F_SUB = "fonts/MPLUSRounded1c-ExtraBold.ttf"

timing = json.load(open(f"{B}/timing.json"))

# ---- タイムライン -------------------------------------------------------------
scenes, t = [], 0.0
for i, (sc, tm) in enumerate(zip(SCENES, timing)):
    speech = tm["end"]
    dur = LEAD + speech + (LAST_TAIL if i == len(SCENES) - 1 else TAIL)
    subs = tm["subs"]
    for k, c in enumerate(subs):
        c["abs"] = t + LEAD + c["start"] - (0.05 if k else 0)  # 字幕は声よりほんの少し先に出す
        c["end"] = t + LEAD + subs[k + 1]["start"] - 0.05 if k + 1 < len(subs) else t + dur
    scenes.append({"start": t, "end": t + dur, "narr_at": t + LEAD, "audio": tm["audio"], **sc, "subs": subs})
    t += dur
TOTAL = t
ENDCARD = scenes[-1] if scenes[-1].get("endcard") else None
FINAL = scenes[-2] if ENDCARD else scenes[-1]  # 「保存して劇場へ」を出す締めのシーン

# シーン内の画像は、script.py の cuts で指定した字幕の区切りで切り替える（2〜3秒ごとに画が変わる）
segments = []  # (start, end, image, scene_start?)
for sc in scenes:
    imgs = sc["image"]
    edges = [sc["start"]] + [sc["subs"][k]["abs"] for k in sc.get("cuts", [])] + [sc["end"]]
    assert len(edges) == len(imgs) + 1, sc["image"]
    for k, name in enumerate(imgs):
        segments.append((edges[k], edges[k + 1], name, k == 0))


# ---- 補間 ---------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_in_out(u):
    u = clamp(u)
    return 0.5 - 0.5 * math.cos(math.pi * u)


def ease_out_back(u, s=1.9):
    u = clamp(u) - 1
    return 1 + u * u * ((s + 1) * u + s)


def ease_out(u):
    return 1 - (1 - clamp(u)) ** 3


# ---- 文字のスプライト -----------------------------------------------------------
def parse(text):
    """'*強調*' を [(文字列, 強調か)] に分ける。"""
    parts, hi = [], False
    for k, p in enumerate(text.split("*")):
        if p:
            parts.append((p, hi))
        hi = not hi
    return parts


def text_sprite(lines, font_path, size, stroke, line_gap=1.18, shadow=10, base=WHITE, max_w=None):
    """白（強調は黄色）＋太い黒フチ＋やわらかい影の文字を RGBA で返す。各行は max_w に収まるまで縮める。"""
    rows = []
    for line in lines:
        s = size
        while True:
            f = ImageFont.truetype(font_path, s)
            wpx = sum(f.getlength(p) for p, _ in parse(line))
            if max_w is None or wpx + 2 * stroke <= max_w or s <= 30:
                break
            s -= 2
        rows.append((line, f, wpx, s))
    pad = stroke + shadow * 3
    tw = int(max(r[2] for r in rows) + 2 * pad)
    heights = [int(r[3] * line_gap) for r in rows]
    th = int(sum(heights) + 2 * pad)
    txt = Image.new("RGBA", (tw, th))
    d = ImageDraw.Draw(txt)
    y = pad
    for (line, f, wpx, s), h in zip(rows, heights):
        x = (tw - wpx) / 2
        for p, hi in parse(line):
            d.text((x, y), p, font=f, fill=YELLOW if hi else base, stroke_width=stroke, stroke_fill=BLACK)
            x += f.getlength(p)
        y += h
    # 影: 文字の形を黒く塗って下にずらしてぼかす
    sh = Image.new("RGBA", txt.size, (0, 0, 0, 0))
    sh.putalpha(txt.getchannel("A").point(lambda a: a * 0.55))
    sh = sh.filter(ImageFilter.GaussianBlur(shadow))
    out = Image.new("RGBA", txt.size)
    out.alpha_composite(sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -shadow * 0.6)))
    out.alpha_composite(txt)
    return out


def badge_sprite(text, fill=YELLOW, fg=BLACK, size=62):
    """角丸のピル型ラベル。"""
    f = ImageFont.truetype(F_TELOP, size)
    tw = f.getlength(text)
    pw, ph = int(tw + size * 1.3), int(size * 1.55)
    m = 14
    img = Image.new("RGBA", (pw + 2 * m, ph + 2 * m))
    sh = Image.new("RGBA", img.size)
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 6, m + pw, m + ph + 6), ph // 2, fill=(0, 0, 0, 140))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + pw, m + ph), ph // 2, fill=fill, outline=BLACK, width=5)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((m + (pw - (bb[2] - bb[0])) / 2 - bb[0], m + (ph - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=fg)
    return img


def place(frame, spr, cx, top, scale=1.0, alpha=1.0, dx=0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    h0 = spr.height
    if abs(scale - 1) > 1e-3:
        spr = spr.resize((max(1, round(spr.width * scale)), max(1, round(spr.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        spr = spr.copy()
        spr.putalpha(spr.getchannel("A").point(lambda a: a * alpha))
    # 拡大縮小は上端ではなくスプライトの中心を基準にする
    frame.alpha_composite(spr, (round(cx - spr.width / 2 + dx), round(top + (h0 - spr.height) / 2)))


# シーンごとのテロップ・ラベル、字幕ごとのスプライトを先に作っておく
for sc in scenes:
    sc["telop_spr"] = text_sprite(sc["telop"], F_TELOP, 132, 13, line_gap=1.12, max_w=980)
    sc["badge_spr"] = badge_sprite(sc["badge"]) if sc["badge"] else None
    for c in sc["subs"]:
        c["spr"] = None if not c["text"] else text_sprite(c["text"].split("\n"), F_SUB, 76, 9, line_gap=1.3, shadow=6, max_w=SUB_MAX_W)


cta_spr = badge_sprite(CTA_TEXT, fill=(254, 44, 85), fg=WHITE, size=78)
CTA_Y = 1170

# VOICEVOX の利用規約に沿ったクレジット表記
credit_spr = text_sprite(["VOICEVOX:青山龍星"], F_SUB, 26, 3, shadow=2)
credit_spr.putalpha(credit_spr.getchannel("A").point(lambda a: a * 0.75))

# 写真の下部に重ねる字幕が読みやすいよう、下からうっすら暗くする
sub_shade = Image.new("RGBA", (W, H))
_sd = ImageDraw.Draw(sub_shade)
for y in range(1280, CARD_Y + CARD_H):
    _sd.line((0, y, W, y), fill=(0, 0, 0, int(150 * ((y - 1280) / (CARD_Y + CARD_H - 1280)) ** 1.5)))

# ---- 画像の下ごしらえ ----------------------------------------------------------
cache = {}
_card_parts = {}


def card_parts(cw, ch):
    """角丸カードのマスクと影（サイズごとにキャッシュ）。"""
    if (cw, ch) not in _card_parts:
        mask = Image.new("L", (cw, ch))
        r = 0 if cw >= W else CARD_R  # 横幅いっぱいのときは角を丸めない
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), r, fill=255)
        sh = Image.new("RGBA", (cw + 120, ch + 120))
        ImageDraw.Draw(sh).rounded_rectangle((60, 76, 60 + cw, 76 + ch), r, fill=(0, 0, 0, 170))
        _card_parts[(cw, ch)] = (mask, sh.filter(ImageFilter.GaussianBlur(22)))
    return _card_parts[(cw, ch)]


# 周辺減光
vig = Image.new("L", (W // 4, H // 4))
vd = vig.load()
for y in range(vig.height):
    for x in range(vig.width):
        dx, dy = (x / vig.width - 0.5) * 1.6, (y / vig.height - 0.5) * 1.15
        vd[x, y] = int(255 * clamp((dx * dx + dy * dy) ** 0.5 - 0.25) * 0.75)
vig = vig.resize((W, H), Image.BICUBIC)
vig_layer = Image.new("RGBA", (W, H), (0, 0, 0, 255))
vig_layer.putalpha(vig)


def load(name):
    if name not in cache:
        src = Image.open(f"{B}/img/{name}").convert("RGB")
        if src.height < 1000:  # 小さい画像（ポスター）は先に高品質に拡大して輪郭を締める
            s = 1100 / src.height
            src = src.resize((round(src.width * s), 1100), Image.LANCZOS)
            src = src.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
        s = (H / 2) / src.height
        bg = src.resize((round(src.width * s), H // 2), Image.LANCZOS)
        x0 = (bg.width - W // 2) // 2
        bg = bg.crop((x0, 0, x0 + W // 2, H // 2)).filter(ImageFilter.GaussianBlur(16))
        bg = ImageEnhance.Brightness(bg).enhance(0.5)
        bg = ImageEnhance.Color(bg).enhance(1.15)
        cache[name] = (src, bg)
    return cache[name]


def render(seg_idx, tt):
    """1つの画像区間のフレーム（背景ぼかし＋角丸カード＋Ken Burns）を描く。"""
    a, b, name, _ = segments[seg_idx]
    src, bg = load(name)
    u = (tt - a) / (b - a)
    zb = 1.04 + 0.06 * u
    frame = bg.transform(
        (W, H), Image.AFFINE,
        (1 / (2 * zb), 0, W / 4 - W / (4 * zb), 0, 1 / (2 * zb), H / 4 - H / (4 * zb)),
        Image.BILINEAR,
    ).convert("RGBA")
    if ENDCARD and a >= ENDCARD["start"] - 1e-6:
        return frame
    # Ken Burns: 偶数番目はズームイン＋右へ、奇数番目はズームアウト＋左へ
    zin = seg_idx % 2 == 0
    e = ease_in_out(u)
    if src.width < src.height:
        # 縦長（ポスター）: カードも縦長にして、横パンせず中央へゆっくり寄る
        bw, bh = round(POSTER_H * src.width / src.height), POSTER_H
        z, pan = 1.0 + 0.08 * e, 0.5
    else:
        bw, bh = CARD_W, CARD_H
        z = 1.0 + 0.13 * (e if zin else 1 - e)
        pan = 0.5 + 0.42 * (e - 0.5) * (1 if zin else -1)
    k = bh / src.height * z
    vw, vh = bw / k, bh / k
    x0 = (src.width - vw) * pan
    y0 = (src.height - vh) * 0.5
    card = src.transform((bw, bh), Image.AFFINE, (1 / k, 0, x0, 0, 1 / k, y0), Image.BICUBIC)
    # 区間の頭でカードが少しだけ寄って落ち着く（パンチイン）
    punch = 1.0 if a == 0 else (1 + 0.07 * (1 - ease_out((tt - a) / 0.35)) if tt >= a else 1.07)
    cw, ch = round(bw * punch), round(bh * punch)
    mask, shadow = card_parts(bw, bh)
    if punch > 1.001:
        card = card.resize((cw, ch), Image.BILINEAR)
        mask = mask.resize((cw, ch), Image.BILINEAR)
        shadow = shadow.resize((round(shadow.width * punch), round(shadow.height * punch)), Image.BILINEAR)
    cx, cy = W // 2, CARD_Y + bh // 2
    frame.alpha_composite(shadow, (cx - shadow.width // 2, cy - shadow.height // 2))
    frame.paste(card, (cx - cw // 2, cy - ch // 2), mask)
    return frame


def xfade_len(boundary):
    """締めのシーンへの切り替えだけは、フラッシュなしのゆっくりしたクロスフェードにする。"""
    return LAST_XFADE if abs(boundary - FINAL["start"]) < 1e-6 else XFADE


def picture_at(tt):
    for i, (a, b, _, _) in enumerate(segments):
        if a <= tt < b or i == len(segments) - 1:
            break
    img = render(i, tt)
    xb, xa = xfade_len(b), xfade_len(a)
    if i + 1 < len(segments) and tt > b - xb / 2:
        img = Image.blend(img, render(i + 1, tt), (tt - (b - xb / 2)) / xb)
    elif i > 0 and tt < a + xa / 2:
        img = Image.blend(render(i - 1, tt), img, (tt - (a - xa / 2)) / xa)
    return img


def portrait_at(tt):
    """その時刻に出ている画像が縦長（ポスター）か。ポスターの間は字幕などをポスター用の位置に出す。"""
    seg = next((s for s in segments if s[0] <= tt < s[1]), segments[-1])
    src, _ = load(seg[2])
    return src.width < src.height


# ---- エンドカード（フォロー誘導） ----------------------------------------------
def thumb_sprite(name, width, angle):
    """過去動画のサムネイルを、白フチ＋影つきの角丸カードにして少し傾ける。"""
    img = Image.open(f"{B}/img/{name}").convert("RGB")
    h = round(img.height * width / img.width)
    img = img.resize((width, h), Image.LANCZOS)
    bd, r, m = 8, 26, 40
    card = Image.new("RGBA", (width + 2 * bd + 2 * m, h + 2 * bd + 2 * m))
    sh = Image.new("RGBA", card.size)
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 14, m + width + 2 * bd, m + h + 2 * bd + 14), r + bd, fill=(0, 0, 0, 160))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(card).rounded_rectangle((m, m, m + width + 2 * bd, m + h + 2 * bd), r + bd, fill=WHITE)
    mask = Image.new("L", (width, h))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, h - 1), r, fill=255)
    card.paste(img, (m + bd, m + bd), mask)
    return card.rotate(angle, resample=Image.BICUBIC, expand=True)


if ENDCARD:
    thumbs = [thumb_sprite(n, 450, ang) for n, ang in zip(ENDCARD["endcard"], (5, -5))]
    follow_spr = badge_sprite("＋ フォロー", fill=(254, 44, 85), fg=WHITE, size=84)


def draw_endcard(frame, st):
    # サムネイル: 下から弾んで、少しずらして2枚出る
    for k, (spr, cx) in enumerate(zip(thumbs, (285, 795))):
        u = (st - 0.12 - 0.14 * k) / 0.4
        if u <= 0:
            continue
        dy = 300 * (1 - ease_out_back(u, 1.4))
        place(frame, spr, cx, 1050 - spr.height / 2 + dy, alpha=clamp(u * 3))
    # フォローボタン: 遅れて出て、ゆっくり脈打つ
    u = (st - 0.5) / 0.3
    if u > 0:
        pulse = 1 + 0.045 * math.sin(2 * math.pi * 1.5 * (st - 0.5)) if u >= 1 else 1
        s = (0.5 + 0.5 * ease_out_back(u)) * pulse
        place(frame, follow_spr, W / 2, 1395, scale=s, alpha=clamp(u * 3))


def frame_at(tt):
    frame = picture_at(tt)
    frame.alpha_composite(vig_layer)
    sc = next(s for s in scenes if tt < s["end"] or s is scenes[-1])
    st = tt - sc["start"]
    portrait = portrait_at(tt)
    if not portrait:
        frame.alpha_composite(sub_shade)
    # シーン頭の白フラッシュ（最初のシーン以外）
    if sc is not scenes[0] and sc is not FINAL and sc is not ENDCARD and st < 0.12:
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - st / 0.12))))
        frame.alpha_composite(fl)
    # ラベル: 左からすべり込む
    top = TELOP_TOP
    if sc["badge_spr"]:
        u = (st - 0.02) / 0.22
        place(frame, sc["badge_spr"], W / 2, top, alpha=clamp(u * 2), dx=-260 * (1 - ease_out(u)))
        top += sc["badge_spr"].height - 8
    # テロップ: 大きく出て弾むように収まる
    u = (st - 0.08) / 0.3 if sc is not scenes[0] else 1.0  # 冒頭は0フレーム目から出ている
    if u > 0:
        tsp = sc["telop_spr"]
        if sc["badge_spr"] is None:
            top = TELOP_TOP + 30
        place(frame, tsp, W / 2, top, scale=0.55 + 0.45 * ease_out_back(u), alpha=clamp(u * 3))
    # 字幕: 区切りごとに小さく弾んで出る
    # 締めでポスターが出ている間は、字幕の代わりに「保存して劇場へ」をポスターの下に出す
    show_subs = not (portrait and sc is FINAL)
    for c in sc["subs"]:
        if show_subs and c["spr"] is not None and c["abs"] <= tt < c["end"]:
            u = (tt - c["abs"]) / 0.16
            spr = c["spr"]
            cy = POSTER_SUB_CY if portrait else SUB_CY
            place(frame, spr, W / 2, cy - spr.height / 2, scale=0.88 + 0.12 * ease_out_back(u, 2.4), alpha=clamp(u * 2.5))
    frame.alpha_composite(credit_spr, (W - credit_spr.width - 24, CARD_Y + 12))
    # 締めの呼びかけ: 日付の字幕と一緒に弾んで出て、最後まで残る
    if sc is FINAL:
        u = (tt - sc["subs"][1]["abs"]) / 0.3
        if u > 0:
            cta_y = POSTER_SUB_CY - cta_spr.height / 2 if portrait else CTA_Y
            place(frame, cta_spr, W / 2, cta_y, scale=0.5 + 0.5 * ease_out_back(u), alpha=clamp(u * 3))
    if sc is ENDCARD:
        draw_endcard(frame, st)
    # ループ再生で冒頭にそのまま戻れるよう、最後は暗転しない
    return frame.convert("RGB")


# ---- 音（ナレーション＋効果音） -----------------------------------------------
inputs, chains = [], []


def add(path, at, vol):
    n = len(chains)
    inputs.extend(["-i", path])
    chains.append(
        f"[{n + 1}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},"
        f"adelay={max(0, round(at * 1000))}:all=1[a{n}]"
    )


# 効果音は効果音ラボ（https://soundeffect-lab.info/）の定番素材。make.sh が build/sfx に取ってくる
SFX = f"{B}/sfx"
for i, sc in enumerate(scenes):
    add(sc["audio"], sc["narr_at"], 1.0)
    if i == 0:
        add(f"{SFX}/shakin1.mp3", 0.02, 0.45)  # タイトルの「シャキーン」
    elif sc is not FINAL:  # 締めのシーンはクロスフェード＋「キラーン」だけにする
        add(f"{SFX}/sceneswitch1.mp3", sc["start"] - 0.06, 0.45)  # 場面転換の「シュッ」
    if sc is FINAL:
        add(f"{SFX}/kira1.mp3", sc["start"] + 0.12, 0.45)  # 締めの「キラーン」
    if sc is ENDCARD:
        add(f"{SFX}/slide1.mp3", sc["start"] + 0.12, 0.3)  # サムネイルが出る
        add(f"{SFX}/slide1.mp3", sc["start"] + 0.26, 0.3)
for a, b, _, scene_start in segments:
    if not scene_start:
        add(f"{SFX}/slide1.mp3", a - 0.05, 0.25)  # シーン内の画像切り替え

mix_in = "".join(f"[a{k}]" for k in range(len(chains)))
fc = ";".join(chains) + (
    f";{mix_in}amix=inputs={len(chains)}:normalize=0,atrim=0:{TOTAL:.3f},"
    "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
)
cmd = [
    "ffmpeg", "-v", "error", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    *inputs,
    "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{TOTAL:.3f}", OUT,
]

if __name__ == "__main__":
    if len(sys.argv) > 2:  # 確認用: 指定秒のフレームを PNG で書き出すだけ
        for s in sys.argv[2:]:
            frame_at(float(s)).save(f"check/t{s}.png")
        sys.exit(0)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(math.ceil(TOTAL * FPS)):
        proc.stdin.write(frame_at(f / FPS).tobytes())
    proc.stdin.close()
    sys.exit(proc.wait())
