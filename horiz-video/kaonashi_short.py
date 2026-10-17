"""YouTube ショート (縦 1080x1920, 約 30 秒)「カオナシの正体」→ 本編 (横動画) へ誘導する

本編 (kaonashi_full.py) の見た目・声・BGM をそのまま使い、縦の画面に組み直す:
  上: 【都市伝説】カオナシの正体 / 真ん中: 場面写真 (ゆっくりズーム) / その下: 字幕
最後は答えを「〇〇人」と隠して「続きは関連動画から」で本編へ。
使い方: python3 horiz-video/kaonashi_short.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import importlib.util
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("kaonashi", HERE / "kaonashi.py")
k = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k)

VW, VH, FPS, SR = 1080, 1920, 30, k.SR
IMG_Y = 820                     # 場面写真の中心の高さ
IMG_W, IMG_H = 1080, 810        # 場面写真 (4:3 に切り出す)
RED = k.RED

# (字幕, 読み, 写真, ズーム, 追加) 追加: key=大きく出す言葉, circle=赤丸, emph=ゆっくり＋エコー＋演出, sfx
SCRIPT = [
    dict(sub="カオナシの正体を|知っているだろうか。", say="カオナシの正体を、知っているだろうか。", img="chihiro/020",
         zoom=(0.47, 0.32, 1.0, 0.47, 0.28, 1.3), sfx="boom"),
    dict(sub="自分の声を持たず|飲み込んだ青蛙の声で話す。", say="自分の声を持たず、飲み込んだ、青蛙の声で話す。",
         img="chihiro/031", zoom=(0.5, 0.35, 1.0, 0.5, 0.28, 1.3), key="他人の声"),
    dict(sub="金で人の心を買おうとし|千尋にだけは拒まれた。", say="金で、人の心を買おうとし、千尋にだけは、拒まれた。",
         img="chihiro/025", zoom=(0.5, 0.6, 1.0, 0.42, 0.72, 1.35), circle=(0.395, 0.745, 0.065), key="拒絶"),
    dict(sub="いくら食べても|満たされない。", say="いくら食べても、満たされない。", img="chihiro/039",
         zoom=(0.62, 0.5, 1.0, 0.65, 0.5, 1.25), sfx="boom"),
    dict(sub="そして、絞り出した言葉は…", say="そして、絞り出した言葉は、", img="chihiro/041",
         zoom=(0.51, 0.3, 1.0, 0.51, 0.22, 1.3)),
    dict(sub="「寂しい」", say="寂しい。", img="chihiro/041", zoom=(0.51, 0.22, 1.3, 0.51, 0.2, 1.6), key="寂しい",
         emph=True, sfx="boom"),
    dict(sub="作中に残された五つの手がかりが示す|カオナシの、本当の正体とは。",
         say="作中に残された、五つの手がかりが示す、カオナシの、本当の正体とは。", img="chihiro/044",
         zoom=(0.3, 0.4, 1.0, 0.25, 0.3, 1.3)),
    dict(sub="カオナシの正体は…|〇〇人だった。", say="カオナシの正体は、まるまるじん、だった。", img="end", emph=True, sfx="boom"),
]
_cache = {}


def bg_of(frame):
    """縦の背景: 場面写真を画面いっぱいに広げて強くぼかし、暗くする"""
    s = VH / frame.height
    big = frame.resize((round(frame.width * s), VH), Image.BILINEAR)
    x = (big.width - VW) // 2
    big = big.crop((x, 0, x + VW, VH)).filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(big, Image.new("RGBA", (VW, VH), (0, 0, 0, 170)))


def vignette():
    if "vig" not in _cache:
        v = Image.new("L", (VW, VH), 0)
        ImageDraw.Draw(v).ellipse((-VW * 0.3, -VH * 0.1, VW * 1.3, VH * 1.1), fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
        dark.putalpha(Image.eval(v, lambda p: int(230 * (1 - p / 255))))
        _cache["vig"] = dark
    return _cache["vig"]


def grain(f):
    key = ("g", (f // 3) % 4)
    if key not in _cache:
        n = np.random.default_rng(key[1]).normal(128, 30, (VH // 3, VW // 3)).clip(0, 255).astype(np.uint8)
        g = Image.fromarray(n, "L").resize((VW, VH), Image.NEAREST)
        im = Image.new("RGBA", (VW, VH), (255, 255, 255, 0))
        im.putalpha(Image.eval(g, lambda p: abs(p - 128) // 6))
        _cache[key] = im
    return _cache[key]


def subtitle(text):
    key = ("sub", text)
    if key not in _cache:
        lines = [k.text_el(t, 64, path=k.SERIF_B, sw=8) for t in text.split("|")]
        lines = [l if l.width <= VW - 20 else l.resize((VW - 20, round(l.height * (VW - 20) / l.width)), Image.LANCZOS)
                 for l in lines]
        im = Image.new("RGBA", (VW, sum(e.height for e in lines) - 18 * (len(lines) - 1)), (0, 0, 0, 0))
        y = 0
        for e in lines:
            im.alpha_composite(e, ((VW - e.width) // 2, y))
            y += e.height - 18
        _cache[key] = im
    return _cache[key]


def header():
    if "head" not in _cache:
        im = Image.new("RGBA", (VW, 320), (0, 0, 0, 0))
        a = k.text_el("【都市伝説】", 70, fill=(235, 30, 40), sw=7)
        b = k.text_el("カオナシの正体", 130, sw=11)
        im.alpha_composite(a, ((VW - a.width) // 2, 10))
        im.alpha_composite(b, ((VW - b.width) // 2, 105))
        _cache["head"] = im
    return _cache["head"]


def scene(s, u):
    """場面写真 (色を落としてズーム) を 4:3 に切り出し、赤丸を描く"""
    frame, (x0, y0, sc) = k.ken_burns(s["img"], s["zoom"], u)
    if "circle" in s:
        im = k.load(s["img"])
        cx, cy, r = s["circle"]
        px, py, pr = (cx * im.width - x0) / sc, (cy * im.height - y0) / sc, r * im.width / sc
        ImageDraw.Draw(frame).ellipse((px - pr, py - pr, px + pr, py + pr), outline=RED + (255,), width=12)
    cw = round(frame.height * IMG_W / IMG_H)
    cx0 = (frame.width - cw) // 2
    return frame, frame.crop((cx0, 0, cx0 + cw, frame.height)).resize((IMG_W, IMG_H), Image.BICUBIC)


def end_card(lt):
    """最後: 「カオナシの正体は…」→ 赤い「〇〇人だった」→ 「続きは関連動画から」"""
    frame, _ = k.ken_burns("chihiro/033", (0.56, 0.37, 1.2, 0.56, 0.37, 1.35), min(lt / 4, 1))
    v = bg_of(frame)
    v = Image.alpha_composite(v, Image.new("RGBA", (VW, VH), (0, 0, 0, 80)))
    k.place(v, k.text_el("カオナシの正体は…", 100), VW / 2, 700, alpha=min(1, lt * 4))
    p = k.ease_back((lt - 0.9) / 0.3)
    k.place(v, k.text_el("〇〇人", 300, fill=(230, 20, 30), stroke="white", sw=12, glow=(120, 0, 0)), VW / 2, 960,
            scale=1.5 - 0.5 * p, alpha=min(1, max(0, (lt - 0.9) * 5)))
    k.place(v, k.text_el("だった", 120), VW / 2, 1170, alpha=min(1, max(0, (lt - 1.1) * 5)))
    if lt > 1.8:
        a = min(1, (lt - 1.8) * 3)
        box = k.text_el("続きは関連動画から", 84, fill=(255, 222, 0), sw=9)
        k.place(v, box, VW / 2, 1450, alpha=a)
        k.place(v, k.text_el("▼", 90, fill=(255, 222, 0), sw=8), VW / 2, 1580 + 12 * np.sin(lt * 8), alpha=a)
    return v


def draw(seg, lt, f):
    s = SCRIPT[seg["i"]]
    if s["img"] == "end":
        v = end_card(lt)
    else:
        u = min(lt / max(seg["dur"], 0.1), 1)
        frame, img = scene(s, u)
        v = bg_of(frame)
        bd = Image.new("RGBA", (IMG_W, IMG_H), (0, 0, 0, 0))
        ImageDraw.Draw(bd).rectangle((0, 0, IMG_W - 1, IMG_H - 1), outline=(150, 0, 0, 255), width=6)
        img.alpha_composite(bd)
        v.alpha_composite(img, (0, IMG_Y - IMG_H // 2))
        if "key" in s:
            p = min(1, max(0, lt - 0.4) / 0.35)
            k.place(v, k.text_el(s["key"], 150, fill=(235, 30, 40), stroke=(10, 10, 10), sw=9, glow=(90, 0, 0)),
                    VW / 2, IMG_Y, scale=1.15 - 0.15 * p, alpha=p)
        sub = subtitle(s["sub"])
        v.alpha_composite(sub, (0, IMG_Y + IMG_H // 2 + 40))
    v.alpha_composite(header())
    v.alpha_composite(vignette())
    v.alpha_composite(grain(f))
    if s.get("emph") or (seg["i"] == 0 and lt < 0.35):   # 決め台詞: 赤いフラッシュと揺れ
        hit = 0.9 if s["img"] == "end" else 0.0
        el = lt - hit
        if 0 <= el < 0.5:
            rng = random.Random(f)
            amp = 22 * (1 - el / 0.5)
            v = v.transform(v.size, Image.AFFINE, (1, 0, rng.uniform(-amp, amp), 0, 1, rng.uniform(-amp, amp)),
                            resample=Image.BILINEAR)
        if 0 <= el < 0.3:
            v.alpha_composite(Image.new("RGBA", (VW, VH), (200, 0, 0, int(120 * (1 - el / 0.3)))))
    ImageDraw.Draw(v).text((VW - 16, VH - 12), k.COPY, font=k.font(k.SANS, 22), fill=(255, 255, 255, 150), anchor="rd")
    return v.convert("RGB")


def main():
    k.SPEED = 1.1
    k.PAUSE = 0.35
    segs, t = [], 0.15
    for i, s in enumerate(SCRIPT):
        a, kana = k.synth(s["say"], k.EMPH_SPEED if s.get("emph") else None)
        if s.get("emph"):
            a = k.echo(a)
        dur = len(a) / SR + (0.3 if s.get("emph") else 0.06)
        segs.append(dict(i=i, start=t, dur=dur, voice=a, kana=kana))
        t += dur
    total = t + 2.2                             # 最後の「続きは関連動画から」を見せる
    n = int(SR * total)
    voice = np.zeros(n + SR)
    for sg in segs:
        a0 = int(sg["start"] * SR)
        voice[a0:a0 + len(sg["voice"])] += sg["voice"]
    voice *= 10 ** (-13 / 20) / k.active_rms(voice)
    ref = k.active_rms(voice)
    buf = voice.copy()
    # BGM (本編と同じ魔王魂「サイバー45」)。声の間は下げる
    bgm = k.load_audio(k.BGM_DIR / k.BGM_DEFAULT)
    bgm = k.looped(bgm / (np.sqrt(np.mean(bgm[np.abs(bgm) > 0.01] ** 2)) + 1e-9), n, int(SR * 1.5))
    v = np.convolve(np.abs(voice[:n]), np.ones(int(SR * 0.3)) / int(SR * 0.3), mode="same")
    on = np.clip(v / (np.max(v) * 0.1 + 1e-9), 0, 1)
    fade = np.minimum(1, np.arange(n) / (SR * 0.5)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.0))
    buf[:n] += bgm * 10 ** ((k.BGM_DB + k.DUCK_DB * on) / 20) * fade * ref
    for sg in segs:
        s = SCRIPT[sg["i"]]
        if s.get("sfx") == "boom":
            c = k.boom()
            hit = 0.9 if s["img"] == "end" else 0.0
            a0 = int((sg["start"] + hit) * SR)
            buf[a0:a0 + len(c)] += (c / k.active_rms(c) * ref * 10 ** (-6 / 20))[: len(buf) - a0]
    wav = k.OUT / "_kaonashi_short.f32"
    buf[:n].astype("<f4").tofile(wav)
    out = k.OUT / "kaonashi_short.mp4"
    cmd = [k.FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(round(total * FPS)):
        tt = f / FPS
        sg = dict(next((g for g in reversed(segs) if g["start"] <= tt), segs[0]), t=tt)
        proc.stdin.write(draw(sg, max(tt - sg["start"], 0), f).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    print("total", round(total, 2))
    for g in segs:
        print(round(g["start"], 2), g["kana"])


if __name__ == "__main__":
    main()
