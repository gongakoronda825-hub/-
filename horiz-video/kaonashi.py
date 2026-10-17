"""YouTube 横動画「カオナシ＝現代人説」 冒頭 1 分のサンプル と サムネイル

1920x1080。場面写真をゆっくりズーム (ケン・バーンズ) させ、下に 2 行字幕、左上に章の札。
台本は 1 文ずつ VOICEVOX で読み、文ごとに写真・ズーム先・赤丸・キーワードを決める。
内容は作中の描写だけ (青蛙の声で話す / 札と金を差し出す / 千尋は受け取らない / 暴れる / 最後は銭婆の家)。
使い方: python3 horiz-video/kaonashi.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("race", ROOT / "race-video" / "make.py")
race = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(race)
font, outlined, place, ease_back = race.font, race.outlined, race.place, race.ease_back
synth, load_sfx, active_rms = race.synth, race.load_sfx, race.active_rms
FFMPEG, OUT, RAW, SR = race.FFMPEG, race.OUT, race.RAW, race.SR

W, H, FPS = 1920, 1080, 30
SPEED = 1.2
GAP = 0.12                  # 文と文の間
RED = (230, 30, 40)
YELLOW = (255, 214, 0)
COPY = "©2001 Studio Ghibli・NDDTM"

# 1 文ずつ: 字幕 (| で改行), 読み (字幕と違うときだけ), 写真,
# ズーム (中心 x, y は写真上の 0〜1, 倍率) の始め→終わり。同じ写真が続くときは前の終わりから始めて途切れさせない,
# 章, 赤丸 (写真上の 0〜1 の x, y, 半径), キーワード (大きく出す言葉), 効果音
SCRIPT = [
    dict(sub="カオナシって、|結局何者だったのか。", img="chihiro/020", zoom=(0.47, 0.35, 1.0, 0.47, 0.32, 1.12)),
    dict(sub="作中の行動を順番に追っていくと、|ある説が浮かび上がります。", img="chihiro/020", zoom=(0.47, 0.32, 1.12, 0.47, 0.28, 1.3)),
    dict(sub="それが…", img="title", sfx="drum-japanese2.mp3"),
    dict(sub="カオナシ＝現代人説です。", say="カオナシ、イコール現代人説です。", img="title", sfx="jean1.mp3"),
    dict(sub="まず注目したいのは、|カオナシには自分の言葉がないこと。", img="chihiro/041", zoom=(0.5, 0.3, 1.05, 0.5, 0.3, 1.2),
         chapter="①自分の言葉がない", sfx="decision22.mp3"),
    dict(sub="カオナシが初めて話すのは、|青蛙を飲み込んだ後。", img="chihiro/031", zoom=(0.5, 0.35, 1.0, 0.5, 0.3, 1.15)),
    dict(sub="しかもその声は、|飲み込んだ青蛙の声なんです。", img="chihiro/031", zoom=(0.5, 0.3, 1.15, 0.5, 0.22, 1.45),
         key="他人の声で話す", sfx="eye-shine1.mp3"),
    dict(sub="つまり、他人を取り込まないと|自分の気持ちすら伝えられない。", img="chihiro/033", zoom=(0.6, 0.4, 1.05, 0.6, 0.4, 1.15)),
    dict(sub="次に、カオナシは千尋の気を引くために|薬湯の札や金を差し出します。",
         say="次に、カオナシは千尋の気を引くために、薬湯のふだや、金を差し出します。",
         img="chihiro/025", zoom=(0.55, 0.55, 1.0, 0.5, 0.65, 1.1), chapter="②物で気を引く", sfx="decision22.mp3"),
    dict(sub="でも千尋は、|金を受け取りませんでした。", img="chihiro/025", zoom=(0.5, 0.65, 1.1, 0.42, 0.72, 1.35),
         circle=(0.395, 0.745, 0.065), key="受け取らない", sfx="eye-shine1.mp3"),
    dict(sub="金をばらまくカオナシに、|従業員たちはごちそうを次々に運びます。",
         say="金をばらまくカオナシに、従業員たちは、ごちそうを次々に運びます。",
         img="chihiro/030", zoom=(0.5, 0.5, 1.0, 0.45, 0.45, 1.12), chapter="③食べても満たされない",
         sfx="decision22.mp3"),
    dict(sub="カオナシはそれを食べ続け、|どんどん大きくなっていく。", img="chihiro/031", zoom=(0.5, 0.45, 1.0, 0.5, 0.35, 1.2),
         key="どんどん巨大化"),
    dict(sub="そして千尋に断られると暴れ出し、|従業員まで飲み込んでしまう。", img="chihiro/033",
         zoom=(0.62, 0.35, 1.0, 0.62, 0.35, 1.2)),
    dict(sub="物で気を引き、|いくら食べても満たされない。", img="chihiro/020", zoom=(0.47, 0.3, 1.35, 0.47, 0.32, 1.15)),
    dict(sub="この姿、どこか|現代の私たちに重なりませんか？", img="chihiro/020", zoom=(0.47, 0.32, 1.15, 0.47, 0.35, 1.0),
         key="現代人そのもの…？"),
    dict(sub="でも本当に注目すべきなのは、|物語の最後に…", say="でも本当に注目すべきなのは、物語の最後に、",
         img="chihiro/044", zoom=(0.25, 0.4, 1.0, 0.25, 0.35, 1.15)),
    dict(sub="カオナシが見つけた|「居場所」なんです。", say="カオナシが見つけた、居場所なんです。",
         img="chihiro/044", zoom=(0.25, 0.35, 1.15, 0.25, 0.3, 1.35), circle=(0.25, 0.24, 0.09), end=True),
]

_cache = {}


def load(name):
    if name not in _cache:
        work, num = name.split("/")
        _cache[name] = Image.open(RAW / work / f"{work}{num}.jpg").convert("RGB")
    return _cache[name]


def ken_burns(name, zoom, u):
    """写真を (cx, cy) に向かって z0→z1 倍にズームした 1920x1080"""
    im = load(name)
    cx0, cy0, z0, cx1, cy1, z1 = zoom           # (中心 x, y, 倍率) の始め → 終わり
    u = u * u * (3 - 2 * u)                   # ゆっくり始まってゆっくり止まる
    z = z0 + (z1 - z0) * u
    cx, cy = cx0 + (cx1 - cx0) * u, cy0 + (cy1 - cy0) * u
    base = max(W / im.width, H / im.height)
    cw, ch = W / (base * z), H / (base * z)
    x0 = min(max(cx * im.width - cw / 2, 0), im.width - cw)
    y0 = min(max(cy * im.height - ch / 2, 0), im.height - ch)
    frame = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    return frame.convert("RGBA"), (x0, y0, cw / W)


def subtitle(text):
    key = ("sub", text)
    if key not in _cache:
        lines = [outlined(t, 66) for t in text.split("|")]
        im = Image.new("RGBA", (W, sum(e.height for e in lines) - 10 * (len(lines) - 1)), (0, 0, 0, 0))
        y = 0
        for e in lines:
            im.alpha_composite(e, ((W - e.width) // 2, y))
            y += e.height - 10
        _cache[key] = im
    return _cache[key]


def tag(text, color, size=46, pad=(26, 6)):
    t = outlined(text, size)
    im = Image.new("RGBA", (t.width + pad[0] * 2, t.height + pad[1] * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=18, fill=color + (240,),
                                         outline=(255, 255, 255, 255), width=4)
    im.alpha_composite(t, pad)
    return im


def title_card(lt, line):
    """「カオナシ＝現代人説」の大見出し。暗くした写真の上に"""
    frame, _ = ken_burns("chihiro/042", (0.76, 0.35, 1.25, 0.76, 0.35, 1.35), min(lt / 4, 1))
    frame = Image.alpha_composite(frame, Image.new("RGBA", (W, H), (0, 0, 0, 150)))
    if line == 0:
        place(frame, outlined("それが…", 110), W / 2, H / 2 - 40, alpha=min(1, lt * 4))
        return frame
    p = ease_back(lt / 0.35)
    a = outlined("カオナシ＝", 170)
    b = outlined("現代人説", 190, fill=RED, stroke="white")
    row = Image.new("RGBA", (a.width + b.width - 20, max(a.height, b.height)), (0, 0, 0, 0))
    row.alpha_composite(a, (0, row.height - a.height))
    row.alpha_composite(b, (a.width - 20, 0))
    place(frame, row, W / 2, H / 2 - 60, scale=1.6 - 0.6 * p)
    return frame


def draw(i, lt, seg):
    s = SCRIPT[i]
    if s["img"] == "title":
        frame = title_card(lt, 0 if s["sub"] == "それが…" else 1)
    else:
        u = min(lt / max(seg["dur"], 0.1), 1)
        frame, (x0, y0, sc) = ken_burns(s["img"], s["zoom"], u)
        if "circle" in s:                       # 赤丸 (写真上の位置を画面上の位置に直す)
            im = load(s["img"])
            cx, cy, r = s["circle"]
            px, py, pr = (cx * im.width - x0) / sc, (cy * im.height - y0) / sc, r * im.width / sc
            p = min(1, lt / 0.25)
            d = ImageDraw.Draw(frame)
            d.arc((px - pr, py - pr, px + pr, py + pr), -90, -90 + 360 * p, fill=RED + (255,), width=14)
            if p >= 1:                          # 横から矢印
                ax = px - pr - 30
                d.polygon([(ax, py), (ax - 70, py - 40), (ax - 70, py + 40)], fill=RED + (255,))
                d.rectangle((ax - 200, py - 16, ax - 68, py + 16), fill=RED + (255,))
    if "key" in s:
        p = ease_back((lt - 0.4) / 0.3)
        place(frame, tag(s["key"], RED, size=72, pad=(36, 10)), W / 2, 330, scale=p, angle=-3)
    if s.get("end") and lt > 0.6:
        place(frame, tag("続きは本編で！", (30, 30, 30), size=56), W - 330, 120, scale=ease_back((lt - 0.6) / 0.3))
    if seg["chapter"]:                          # 左上の章の札 (章が変わったら跳ねて出る)
        el = seg["t"] - seg["chapter_t"]
        place(frame, tag(seg["chapter"], RED), 60 + tag(seg["chapter"], RED).width / 2, 70,
              scale=ease_back(el / 0.3) if el < 0.3 else 1)
    if s["img"] != "title":                     # 字幕の下に薄い帯
        band = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
        ImageDraw.Draw(band).rectangle((0, 40, W, 230), fill=(0, 0, 0, 120))
        frame.alpha_composite(band.filter(ImageFilter.GaussianBlur(25)), (0, H - 230))
        sub = subtitle(s["sub"])
        frame.alpha_composite(sub, (0, H - 40 - sub.height))
    ImageDraw.Draw(frame).text((W - 20, H - 12), COPY, font=font(22, b"Medium"), fill=(255, 255, 255, 170),
                               anchor="rd")
    return frame.convert("RGB")


# ---- サムネイル (1280x720) -------------------------------------------------------
def thumbnail(path):
    TW, TH = 1280, 720
    im = load("chihiro/025")                    # 千尋に手を差し出すカオナシ
    s = TH / im.height * 1.12
    big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0 = int(big.width * 0.62 - TW * 0.55)      # カオナシの顔が中央やや右に来るように
    th = big.crop((x0, 0, x0 + TW, TH)).convert("RGBA")
    th = ImageEnhance.Brightness(th).enhance(0.8)
    v = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))   # 周りと下を暗く (文字を読みやすく)
    vd = ImageDraw.Draw(v)
    vd.rectangle((0, 0, TW, TH), outline=(0, 0, 0, 170), width=100)
    vd.rectangle((0, TH - 260, TW, TH), fill=(0, 0, 0, 150))
    th.alpha_composite(v.filter(ImageFilter.GaussianBlur(50)))
    # 上の小見出し
    small = outlined("カオナシの正体は…", 74)
    th.alpha_composite(small, (30, 18))
    # 下の大見出し: 「現代人」だけ赤。横幅に収まるよう縮める
    a = outlined("実は", 130)
    b = outlined("現代人", 200, fill=RED, stroke="white")
    c = outlined("だった", 150)
    row = Image.new("RGBA", (a.width + b.width + c.width - 60, b.height), (0, 0, 0, 0))
    row.alpha_composite(a, (0, b.height - a.height - 18))
    row.alpha_composite(b, (a.width - 30, 0))
    row.alpha_composite(c, (a.width + b.width - 60, b.height - c.height - 18))
    k = min(1.0, (TW - 50) / row.width)
    row = row.resize((round(row.width * k), round(row.height * k)), Image.LANCZOS)
    th.alpha_composite(row, ((TW - row.width) // 2, TH - row.height + 4))
    # 吹き出し (縦書き)
    bx, by, bw, bh = 1050, 110, 175, 320
    bub = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bub)
    bd.polygon([(bx + 40, by + bh - 80), (bx - 50, by + bh + 20), (bx + 80, by + bh - 30)], fill=(255, 255, 255, 255),
               outline=(0, 0, 0, 255))
    bd.ellipse((bx, by, bx + bw, by + bh), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=5)
    for k2, ch in enumerate(["あ", "︙", "あ", "︙"]):
        bd.text((bx + bw / 2, by + 62 + k2 * 66), ch, font=font(66), fill=(20, 20, 20), anchor="mm")
    th.alpha_composite(bub)
    ImageDraw.Draw(th).rectangle((0, 0, TW - 1, TH - 1), outline=RED + (255,), width=14)   # 赤い枠
    th.convert("RGB").save(path, quality=95)


# ---- 組み立て ---------------------------------------------------------------
def main():
    OUT.mkdir(exist_ok=True)
    thumbnail(OUT / "kaonashi_thumbnail.jpg")
    segs, t, chapter, chapter_t = [], 0.3, None, 0.0
    for i, s in enumerate(SCRIPT):
        a, kana = synth(s.get("say", s["sub"].replace("|", "")), SPEED)
        if "chapter" in s:
            chapter, chapter_t = s["chapter"], t
        dur = len(a) / SR + (0.35 if s["img"] == "title" else GAP)
        segs.append(dict(i=i, start=t, dur=dur, voice=a, kana=kana, chapter=chapter, chapter_t=chapter_t))
        t += dur
    total = t + 0.8
    # 音
    buf = np.zeros(int(SR * total) + SR)
    voice = np.zeros_like(buf)
    for sg in segs:
        a0 = int(sg["start"] * SR)
        voice[a0:a0 + len(sg["voice"])] += sg["voice"]
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    target = active_rms(voice) * 10 ** (-13 / 20)
    for sg in segs:
        name = SCRIPT[sg["i"]].get("sfx")
        if name:
            c = load_sfx(name)
            a0 = int(max(0, sg["start"] - (0.05 if name != "drum-japanese2.mp3" else 0)) * SR)
            buf[a0:a0 + len(c)] += (c * target / active_rms(c))[: len(buf) - a0]
    wav = OUT / "_kaonashi_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(wav)
    out = OUT / "kaonashi_sample.mp4"
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(round(total * FPS)):
        tt = f / FPS
        sg = next((g for g in reversed(segs) if g["start"] <= tt), segs[0])
        sg = dict(sg, t=tt)
        lt = tt - sg["start"]
        frame = draw(sg["i"], max(lt, 0), sg)
        if tt > total - 0.6:                    # 最後は暗転
            frame = Image.blend(frame, Image.new("RGB", (W, H)), min(1, (tt - (total - 0.6)) / 0.5))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(total=round(total, 2), lines=[(round(g["start"], 2), SCRIPT[g["i"]]["sub"], g["kana"]) for g in segs])
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
