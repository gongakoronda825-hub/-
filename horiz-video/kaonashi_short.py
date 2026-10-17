"""YouTube ショート (縦 1080x1920, 約 30 秒)「カオナシの正体」→ 本編 (横動画) へ誘導する

本編 (kaonashi_full.py) の序盤と同じ見た目・声・BGM。縦の画面いっぱいに暗い場面写真をズームし、下に字幕。
答えは「現代人だった」と言い切り、「なぜ？」と「続きは関連動画で」で本編へ。
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
RED = k.RED

# 本編の序盤と同じ流れ。答え (現代人) は言い切り、「なぜ？」で本編へ誘導する
# img: 場面写真 / "title": 大見出し / "end": 続きは関連動画で。zoom は縦に切り出す中心 (x, y) と倍率の始め→終わり
SCRIPT = [
    dict(sub="千と千尋の神隠しに登場する|謎の存在、カオナシ。", say="千と千尋の神隠しに登場する、謎の存在、カオナシ。",
         img="chihiro/020", zoom=(0.47, 0.4, 1.0, 0.47, 0.38, 1.1), sfx="boom"),
    dict(sub="顔もなく、声もなく|どこから来たのかも分からない。", say="顔もなく、声もなく、どこから来たのかも分からない。",
         img="chihiro/020", zoom=(0.47, 0.38, 1.1, 0.47, 0.3, 1.35)),
    dict(sub="しかし、その行動を|一つずつ追っていくと…", say="しかし、その行動を、一つずつ追っていくと、",
         img="chihiro/041", zoom=(0.51, 0.45, 1.0, 0.51, 0.4, 1.12)),
    dict(sub="ある恐ろしい説が|浮かび上がる。", say="ある、恐ろしい説が、浮かび上がる。",
         img="chihiro/041", zoom=(0.51, 0.4, 1.12, 0.51, 0.3, 1.35)),
    dict(sub="それが…", say="それが、", img="title", emph=True),
    dict(sub="カオナシの正体は、現代人だった。", say="カオナシの正体は、現代人だった。", img="title", emph=True, sfx="boom"),
    dict(sub="なぜ、カオナシは|現代人なのか。", say="なぜ、カオナシは、現代人なのか。",
         img="chihiro/033", zoom=(0.56, 0.45, 1.0, 0.56, 0.4, 1.15)),
    dict(sub="その答えは、作中に残された|五つの手がかりに隠されていた。", say="その答えは、作中に残された、五つの手がかりに、隠されていた。",
         img="chihiro/044", zoom=(0.25, 0.45, 1.0, 0.25, 0.4, 1.15)),
    dict(sub="続きは、関連動画で。", say="続きは、関連動画で。", img="end"),
]
_cache = {}


def ken_burns_v(name, zoom, u):
    """縦の画面いっぱいに場面写真を切り出してズーム (色は本編と同じ都市伝説風)"""
    im = k.graded(name)
    cx0, cy0, z0, cx1, cy1, z1 = zoom
    u = u * u * (3 - 2 * u)
    z = z0 + (z1 - z0) * u
    cx, cy = cx0 + (cx1 - cx0) * u, cy0 + (cy1 - cy0) * u
    ch = im.height / z
    cw = ch * VW / VH
    x0 = min(max(cx * im.width - cw / 2, 0), im.width - cw)
    y0 = min(max(cy * im.height - ch / 2, 0), im.height - ch)
    return im.resize((VW, VH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch)).convert("RGBA")


def vignette():
    if "vig" not in _cache:
        v = Image.new("L", (VW, VH), 0)
        ImageDraw.Draw(v).ellipse((-VW * 0.35, -VH * 0.12, VW * 1.35, VH * 1.12), fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
        dark.putalpha(Image.eval(v, lambda p: int(235 * (1 - p / 255))))
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
        lines = [k.text_el(t, 70, path=k.SERIF_B, sw=8) for t in text.split("|")]
        lines = [l if l.width <= VW - 20 else l.resize((VW - 20, round(l.height * (VW - 20) / l.width)), Image.LANCZOS)
                 for l in lines]
        im = Image.new("RGBA", (VW, sum(e.height for e in lines) - 18 * (len(lines) - 1)), (0, 0, 0, 0))
        y = 0
        for e in lines:
            im.alpha_composite(e, ((VW - e.width) // 2, y))
            y += e.height - 18
        _cache[key] = im
    return _cache[key]


def title_frame(s, lt):
    """大見出し: 暗くした電車のカオナシの上に「カオナシの正体は」/「現代人だった」"""
    v = ken_burns_v("chihiro/042", (0.76, 0.45, 1.0, 0.76, 0.42, 1.12), min(lt / 5, 1))
    v = Image.alpha_composite(v, Image.new("RGBA", (VW, VH), (0, 0, 0, 175)))
    if s["sub"] == "それが…":
        k.place(v, k.text_el("それが…", 130), VW / 2, VH / 2 - 60, alpha=min(1, lt * 3))
        return v
    k.place(v, k.text_el("カオナシの正体は", 110), VW / 2, VH / 2 - 260, alpha=min(1, lt / 0.25))
    q = k.ease_back((lt - 0.55) / 0.3)
    el = k.text_el("現代人", 280, fill=(235, 30, 40), stroke=(10, 10, 10), sw=12, glow=(120, 0, 0))
    k.place(v, el, VW / 2, VH / 2 - 20, scale=1.5 - 0.5 * q, alpha=min(1, max(0, (lt - 0.55) * 5)))
    k.place(v, k.text_el("だった", 150, fill=(235, 30, 40), stroke=(10, 10, 10), sw=9, glow=(120, 0, 0)), VW / 2,
            VH / 2 + 230, alpha=min(1, max(0, (lt - 0.7) * 5)))
    return v


def end_frame(lt):
    v = ken_burns_v("chihiro/041", (0.51, 0.35, 1.2, 0.51, 0.3, 1.35), min(lt / 3, 1))
    v = Image.alpha_composite(v, Image.new("RGBA", (VW, VH), (0, 0, 0, 120)))
    k.place(v, k.text_el("続きは関連動画で", 100, fill=(255, 222, 0), sw=10), VW / 2, 1300, alpha=min(1, lt * 4))
    k.place(v, k.text_el("▼", 100, fill=(255, 222, 0), sw=8), VW / 2, 1450 + 14 * np.sin(lt * 8), alpha=min(1, lt * 4))
    return v


def draw(seg, lt, f):
    s = SCRIPT[seg["i"]]
    if s["img"] == "title":
        v = title_frame(s, lt)
    elif s["img"] == "end":
        v = end_frame(lt)
    else:
        v = ken_burns_v(s["img"], s["zoom"], min(lt / max(seg["dur"], 0.1), 1))
    v.alpha_composite(vignette())
    if s["img"] not in ("title", "end"):
        sub = subtitle(s["sub"])
        v.alpha_composite(sub, (0, 1380))
    v.alpha_composite(grain(f))
    if s.get("emph") and s["sub"] != "それが…":     # 決め台詞: ノイズ・揺れ・赤いフラッシュ
        el = lt - 0.55
        if 0 <= el < 0.35:
            v = glitch_v(v, 1 - el / 0.35, f)
        if 0 <= el < 0.5:
            rng = random.Random(f)
            amp = 22 * (1 - el / 0.5)
            v = v.transform(v.size, Image.AFFINE, (1, 0, rng.uniform(-amp, amp), 0, 1, rng.uniform(-amp, amp)),
                            resample=Image.BILINEAR)
        if 0 <= el < 0.3:
            v.alpha_composite(Image.new("RGBA", (VW, VH), (200, 0, 0, int(120 * (1 - el / 0.3)))))
    rng = random.Random(f * 7)                  # ちらつき (本編の序盤と同じ)
    if rng.random() < 0.08:
        v.alpha_composite(Image.new("RGBA", (VW, VH), (0, 0, 0, rng.randint(20, 50))))
    if f < 15:                                  # 暗闇から始まる
        v = Image.blend(Image.new("RGBA", (VW, VH), (0, 0, 0, 255)), v, f / 15)
    ImageDraw.Draw(v).text((VW - 16, VH - 12), k.COPY, font=k.font(k.SANS, 22), fill=(255, 255, 255, 150), anchor="rd")
    return v.convert("RGB")


def glitch_v(frame, amount, seed):
    rng = random.Random(seed)
    rgb = frame.convert("RGB")
    r, g, b = rgb.split()
    sh = int(18 * amount)
    rgb = Image.merge("RGB", (r.transform(rgb.size, Image.AFFINE, (1, 0, sh, 0, 1, 0)), g,
                              b.transform(rgb.size, Image.AFFINE, (1, 0, -sh, 0, 1, 0))))
    for _ in range(int(10 * amount)):
        y, h = rng.randint(0, VH - 60), rng.randint(8, 60)
        rgb.paste(rgb.crop((0, y, VW, y + h)), (rng.randint(-80, 80), y))
    return rgb.convert("RGBA")


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
    total = t + 1.0                             # 最後の「続きは関連動画で」を少し見せる
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
            hit = 0.55 if s["img"] == "title" else 0.0
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
