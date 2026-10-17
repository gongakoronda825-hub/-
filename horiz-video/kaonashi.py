"""YouTube 横動画「カオナシ＝現代人説」 冒頭 1 分のサンプル と サムネイル (都市伝説風)

1920x1080。暗く色を落とした場面写真をゆっくりズームし、周りを暗く、フィルムのざらつきとちらつきを重ねる。
文字は明朝体。章の切り替わりはノイズの走る演出と「ザザッ」、決め台詞で低い「ドーン」。後ろに低い持続音を薄く流す。
台本は 1 文ずつ VOICEVOX (青山龍星 しっとり) で読み、文ごとに写真・ズーム先・赤丸・キーワードを決める。
内容は作中の描写だけ (青蛙の声で話す / 札と金を差し出す / 千尋は受け取らない / 食べて大きくなる / 暴れる / 最後は銭婆の家)。
使い方: python3 horiz-video/kaonashi.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import importlib.util
import io
import json
import random
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("race", ROOT / "race-video" / "make.py")
race = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(race)
place, ease_back, active_rms = race.place, race.ease_back, race.active_rms
FFMPEG, OUT, RAW, SR, ENGINE = race.FFMPEG, race.OUT, race.RAW, race.SR, race.ENGINE

W, H, FPS = 1920, 1080, 30
SPEAKER = 84                # 青山龍星 しっとり (落ち着いた男性)
SPEED = 1.1
GAP = 0.25                  # 文と文の間 (都市伝説らしく少しだけ間をとる)
RED = (210, 20, 30)
COPY = "©2001 Studio Ghibli・NDDTM"
SERIF = ROOT / "ghibli-video" / "fonts" / "NotoSerifJP-Black.ttf"
SERIF_B = ROOT / "ghibli-video" / "fonts" / "NotoSerifJP-Bold.ttf"
SANS = ROOT / "ghibli-video" / "fonts" / "NotoSansJP.ttf"
ANTIQUE = ROOT / "ghibli-video" / "fonts" / "ZenAntique.ttf"   # 古い印刷物のような明朝 (サムネの見出し)
BRUSH = ROOT / "ghibli-video" / "fonts" / "YujiBoku.ttf"       # かすれた筆文字 (サムネの左右の 2 文字)

# 1 文ずつ: 字幕 (| で改行), 読み (字幕と違うときだけ), 写真,
# ズーム (中心 x, y は写真上の 0〜1, 倍率) の始め→終わり。同じ写真が続くときは前の終わりから始めて途切れさせない,
# 章, 赤丸 (写真上の 0〜1 の x, y, 半径), キーワード (大きく出す言葉), 効果音 (boom: 低いドーン, glitch: ノイズ)
SCRIPT = [
    dict(sub="千と千尋の神隠しに登場する|謎の存在、カオナシ。", say="千と千尋の神隠しに登場する、謎の存在、カオナシ。",
         img="chihiro/020", zoom=(0.47, 0.35, 1.0, 0.47, 0.32, 1.12), sfx="boom"),
    dict(sub="顔もなく、声もなく|どこから来たのかも分からない。", say="顔もなく、声もなく、どこから来たのかも分からない。",
         img="chihiro/020", zoom=(0.47, 0.32, 1.12, 0.47, 0.25, 1.4)),
    dict(sub="しかし、その行動を一つずつ追っていくと…", say="しかし、その行動を、一つずつ追っていくと、",
         img="chihiro/041", zoom=(0.5, 0.3, 1.0, 0.5, 0.3, 1.15)),
    dict(sub="ある恐ろしい説が浮かび上がる。", say="ある、恐ろしい説が、浮かび上がる。",
         img="chihiro/041", zoom=(0.5, 0.3, 1.15, 0.52, 0.25, 1.35)),
    dict(sub="それが…", img="title"),
    dict(sub="カオナシの正体は、現代人だった。", img="title", sfx="boom"),
    dict(sub="第一の手がかり。|カオナシには、自分の声がない。", say="第一の手がかり。カオナシには、自分の声がない。",
         img="chihiro/031", zoom=(0.5, 0.35, 1.0, 0.5, 0.3, 1.12), chapter=("第一の手がかり", "自分の声がない"),
         sfx="glitch"),
    dict(sub="カオナシが初めて言葉を発するのは|青蛙を飲み込んだ後。",
         say="カオナシが、初めて言葉を発するのは、青蛙を、飲み込んだ後。",
         img="chihiro/031", zoom=(0.5, 0.3, 1.12, 0.5, 0.25, 1.3)),
    dict(sub="そして、その声は…|飲み込まれた青蛙の声だった。", say="そして、その声は、飲み込まれた、青蛙の声だった。",
         img="chihiro/031", zoom=(0.5, 0.25, 1.3, 0.5, 0.22, 1.5), key="他人の声", sfx="boom"),
    dict(sub="他人を取り込まなければ|自分の気持ちすら語れない存在。",
         say="他人を取り込まなければ、自分の気持ちすら、語れない存在。",
         img="chihiro/033", zoom=(0.62, 0.38, 1.0, 0.62, 0.38, 1.15)),
    dict(sub="第二の手がかり。|カオナシは、物で人の心を買おうとする。",
         say="第二の手がかり。カオナシは、物で、人の心を買おうとする。",
         img="chihiro/025", zoom=(0.55, 0.55, 1.0, 0.5, 0.65, 1.1), chapter=("第二の手がかり", "物で心を買う"),
         sfx="glitch"),
    dict(sub="千尋の気を引くために差し出したのは|薬湯の札、そして…金。",
         say="千尋の気を引くために、差し出したのは、薬湯のふだ、そして、金。",
         img="chihiro/025", zoom=(0.5, 0.65, 1.1, 0.45, 0.7, 1.22)),
    dict(sub="だが千尋は|それを受け取らなかった。", say="だが千尋は、それを、受け取らなかった。",
         img="chihiro/025", zoom=(0.45, 0.7, 1.22, 0.42, 0.72, 1.4), circle=(0.395, 0.745, 0.065), key="拒絶",
         sfx="boom"),
    dict(sub="第三の手がかり。|満たされない欲望。", say="第三の手がかり。満たされない、欲望。",
         img="chihiro/030", zoom=(0.5, 0.5, 1.0, 0.47, 0.47, 1.1), chapter=("第三の手がかり", "満たされない欲望"),
         sfx="glitch"),
    dict(sub="金をばらまくカオナシのもとに|ごちそうが次々と運ばれる。",
         say="金をばらまくカオナシのもとに、ごちそうが、次々と運ばれる。",
         img="chihiro/030", zoom=(0.47, 0.47, 1.1, 0.45, 0.45, 1.22)),
    dict(sub="カオナシはそれを食べ続け|みるみる巨大化していく。", say="カオナシは、それを食べ続け、みるみる、巨大化していく。",
         img="chihiro/031", zoom=(0.5, 0.45, 1.0, 0.5, 0.35, 1.25), key="巨大化"),
    dict(sub="そして千尋に拒まれた後…|従業員まで飲み込み、暴れ出す。",
         say="そして、千尋に拒まれた後、従業員まで飲み込み、暴れ出す。",
         img="chihiro/033", zoom=(0.62, 0.35, 1.0, 0.64, 0.33, 1.25), sfx="boom"),
    dict(sub="物で心を買おうとし|いくら手に入れても満たされない。",
         say="物で心を買おうとし、いくら手に入れても、満たされない。",
         img="chihiro/020", zoom=(0.47, 0.3, 1.4, 0.47, 0.32, 1.15)),
    dict(sub="その姿は…画面の前の|私たちそのものなのかもしれない。",
         say="その姿は、画面の前の、私たちそのものなのかもしれない。",
         img="chihiro/020", zoom=(0.47, 0.32, 1.15, 0.47, 0.35, 1.0), key="私たち…？"),
    dict(sub="だが、この話には続きがある。", say="だが、この話には、続きがある。",
         img="chihiro/044", zoom=(0.25, 0.4, 1.0, 0.25, 0.35, 1.12), sfx="glitch"),
    dict(sub="物語の最後に、カオナシがたどり着いた場所。|そこに、この説の本当の答えが隠されていた。",
         say="物語の最後に、カオナシがたどり着いた場所。そこに、この説の、本当の答えが、隠されていた。",
         img="chihiro/044", zoom=(0.25, 0.35, 1.12, 0.25, 0.3, 1.4), circle=(0.25, 0.24, 0.09), end=True),
]

_cache = {}


def font(path, size):
    key = ("f", str(path), size)
    if key not in _cache:
        f = ImageFont.truetype(str(path), size)
        if path == SANS:
            f.set_variation_by_name(b"Black")
        _cache[key] = f
    return _cache[key]


def text_el(text, size, fill="white", stroke="black", path=SERIF, sw=None, glow=None):
    """1 行の文字 (フチ付き)。glow を渡すと後ろにぼんやり光らせる"""
    key = ("t", text, size, fill, stroke, str(path), sw, glow)
    if key not in _cache:
        f = font(path, size)
        sw = sw if sw is not None else max(4, size // 10)
        w = int(f.getlength(text)) + sw * 2 + 40
        h = int(size * 1.45) + sw * 2
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if glow:
            g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(g).text((20 + sw, sw), text, font=f, fill=glow + (255,), stroke_width=sw + 8,
                                   stroke_fill=glow + (255,))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(im).text((20 + sw, sw), text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
        _cache[key] = im
    return _cache[key]


def load(name):
    if name not in _cache:
        work, num = name.split("/")
        _cache[name] = Image.open(RAW / work / f"{work}{num}.jpg").convert("RGB")
    return _cache[name]


def graded(name):
    """都市伝説風の色: 彩度を落とし、暗く、少し青緑に寄せる"""
    key = ("g", name)
    if key not in _cache:
        im = load(name)
        im = ImageEnhance.Color(im).enhance(0.45)
        im = ImageEnhance.Brightness(im).enhance(0.72)
        im = ImageEnhance.Contrast(im).enhance(1.15)
        _cache[key] = Image.blend(im, Image.new("RGB", im.size, (20, 40, 50)), 0.12)
    return _cache[key]


def ken_burns(name, zoom, u):
    im = graded(name)
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


def vignette():
    if "vig" not in _cache:
        v = Image.new("L", (W, H), 0)
        ImageDraw.Draw(v).ellipse((-W * 0.15, -H * 0.25, W * 1.15, H * 1.25), fill=255)
        v = v.filter(ImageFilter.GaussianBlur(160))
        dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dark.putalpha(Image.eval(v, lambda p: int(235 * (1 - p / 255))))
        _cache["vig"] = dark
    return _cache["vig"]


def grain(f):
    """フィルムのざらつき (4 枚を 3 フレームずつ使い回す。毎フレーム変えるとファイルが大きくなりすぎる)"""
    f //= 3
    k = ("grain", f % 4)
    if k not in _cache:
        rng = np.random.default_rng(f % 4)
        n = rng.normal(128, 30, (H // 3, W // 3)).clip(0, 255).astype(np.uint8)
        g = Image.fromarray(n, "L").resize((W, H), Image.NEAREST)
        im = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        im.putalpha(Image.eval(g, lambda p: abs(p - 128) // 6))
        _cache[k] = im
    return _cache[k]


def glitch(frame, amount, seed):
    """横にずれる帯と色ずれ (章の切り替わりに一瞬だけ)"""
    rng = random.Random(seed)
    rgb = frame.convert("RGB")
    r, g, b = rgb.split()
    sh = int(18 * amount)
    rgb = Image.merge("RGB", (r.transform(rgb.size, Image.AFFINE, (1, 0, sh, 0, 1, 0)), g,
                              b.transform(rgb.size, Image.AFFINE, (1, 0, -sh, 0, 1, 0))))
    for _ in range(int(8 * amount)):
        y, h = rng.randint(0, H - 60), rng.randint(8, 60)
        strip = rgb.crop((0, y, W, y + h))
        rgb.paste(strip, (rng.randint(-80, 80), y))
    return rgb.convert("RGBA")


def subtitle(text):
    key = ("sub", text)
    if key not in _cache:
        lines = [text_el(t, 62, path=SERIF_B, sw=7) for t in text.split("|")]
        im = Image.new("RGBA", (W, sum(e.height for e in lines) - 18 * (len(lines) - 1)), (0, 0, 0, 0))
        y = 0
        for e in lines:
            im.alpha_composite(e, ((W - e.width) // 2, y))
            y += e.height - 18
        _cache[key] = im
    return _cache[key]


def chapter_el(ch):
    """左上の章: 黒い帯に赤い縦線、「第一の手がかり」(小) と 見出し (大)"""
    key = ("ch", ch)
    if key not in _cache:
        a = text_el(ch[0], 34, fill=(230, 60, 60), sw=0)
        b = text_el(ch[1], 54, sw=0)
        w = max(a.width, b.width) + 30
        im = Image.new("RGBA", (w, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, w, 150), fill=(0, 0, 0, 170))
        d.rectangle((0, 0, 10, 150), fill=RED + (255,))
        im.alpha_composite(a, (12, 4))
        im.alpha_composite(b, (12, 50))
        _cache[key] = im
    return _cache[key]


def chapter_card(s, lt):
    """章の扉: 暗くした写真の上に「第一の手がかり」(赤・小) と章の名前 (白・大)。ノイズが走って出る"""
    frame, _ = ken_burns(s["bg"], (0.5, 0.4, 1.1, 0.5, 0.4, 1.2), min(lt / 4, 1))
    frame = Image.alpha_composite(frame, Image.new("RGBA", (W, H), (0, 0, 0, 185)))
    place(frame, text_el(s["chapter"][0], 70, fill=(235, 30, 40), glow=(90, 0, 0)), W / 2, H / 2 - 110,
          alpha=min(1, lt * 4))
    place(frame, text_el(f"「{s['chapter'][1]}」", 140), W / 2, H / 2 + 50, alpha=min(1, max(0, lt - 0.3) * 4))
    return frame


def title_card(lt, line):
    frame, _ = ken_burns("chihiro/042", (0.76, 0.35, 1.25, 0.76, 0.35, 1.4), min(lt / 5, 1))
    frame = Image.alpha_composite(frame, Image.new("RGBA", (W, H), (0, 0, 0, 175)))
    if line == 0:
        place(frame, text_el("それが…", 110), W / 2, H / 2 - 40, alpha=min(1, lt * 3))
        return frame
    place(frame, text_el("カオナシの正体は", 96), W / 2, H / 2 - 170, alpha=min(1, lt / 0.25))
    q = ease_back((lt - 0.55) / 0.3)
    place(frame, text_el("現代人だった", 220, fill=(235, 30, 40), stroke=(10, 10, 10), sw=10, glow=(120, 0, 0)),
          W / 2, H / 2 + 60, scale=1.5 - 0.5 * q, alpha=min(1, max(0, (lt - 0.55) * 5)))
    return frame


def draw(seg, lt, f):
    s = SCRIPT[seg["i"]]
    if s["img"] == "title":
        frame = title_card(lt, 0 if s["sub"] == "それが…" else 1)
    elif s["img"] == "chapter":
        frame = chapter_card(s, lt)
    else:
        u = min(lt / max(seg["dur"], 0.1), 1)
        frame, (x0, y0, sc) = ken_burns(s["img"], s["zoom"], u)
        if "circle" in s:                       # 赤丸 (写真上の位置を画面上の位置に直す) と矢印
            im = load(s["img"])
            cx, cy, r = s["circle"]
            px, py, pr = (cx * im.width - x0) / sc, (cy * im.height - y0) / sc, r * im.width / sc
            p = min(1, max(0, lt - 0.3) / 0.3)
            d = ImageDraw.Draw(frame)
            if p > 0:
                d.arc((px - pr, py - pr, px + pr, py + pr), -90, -90 + 360 * p, fill=RED + (255,), width=12)
    frame.alpha_composite(vignette())
    if "key" in s:                              # キーワード: 赤い明朝がにじんで出る
        p = min(1, max(0, lt - 0.5) / 0.4)
        place(frame, text_el(s["key"], 130, fill=(235, 30, 40), stroke=(10, 10, 10), sw=8, glow=(90, 0, 0)),
              W / 2, 330, scale=1.15 - 0.15 * p, alpha=p)
    if s.get("end") and lt > 1.0:
        place(frame, text_el("続きは本編で", 64, fill=(235, 30, 40), glow=(90, 0, 0)), W - 300, 110,
              alpha=min(1, (lt - 1.0) / 0.5))
    if seg["chapter"] and s["img"] not in ("title", "chapter"):   # 左上の章 (変わったら左から滑り込む)
        el = seg["t"] - seg["chapter_t"]
        ce = chapter_el(seg["chapter"])
        dx = 0 if el > 0.4 else -ce.width * (1 - ease_back(el / 0.4))
        place(frame, ce, ce.width / 2 + dx, 40 + ce.height / 2)
    if s["img"] not in ("title", "chapter"):
        sub = subtitle(s["sub"])
        frame.alpha_composite(sub, (0, H - 50 - sub.height))
    frame.alpha_composite(grain(f))
    if s.get("sfx") == "glitch" and lt < 0.35:  # 章の切り替わり: ノイズが走る
        frame = glitch(frame, 1 - lt / 0.35, f)
    rng = random.Random(f * 7)                  # ちらつき (明るさがわずかに揺れる)
    if rng.random() < 0.08:
        frame.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, rng.randint(20, 50))))
    ImageDraw.Draw(frame).text((W - 20, H - 12), COPY, font=font(SANS, 22), fill=(255, 255, 255, 150), anchor="rd")
    return frame.convert("RGB")


# ---- 音 -----------------------------------------------------------------------
def post(path, params, body=b""):
    req = urllib.request.Request(f"{ENGINE}{path}?{urllib.parse.urlencode(params)}", data=body,
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def synth(text):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            if m.get("consonant") and m["consonant_length"] < 0.045:
                m["consonant_length"] = 0.045
    q.update(speedScale=SPEED, pauseLengthScale=0.8, prePhonemeLength=0.0, postPhonemeLength=0.05,
             outputSamplingRate=SR, outputStereo=False)
    with wave.open(io.BytesIO(post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode()))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return (a[idx[0]: idx[-1] + 1] if len(idx) else a), q["kana"]


def boom():
    """低い「ドーン」: 下がっていく低音＋少しの雑音"""
    t = np.arange(int(SR * 2.0)) / SR
    a = np.sin(2 * np.pi * np.cumsum(38 + 50 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    return a + np.random.default_rng(1).normal(0, 1, len(t)) * np.exp(-t * 18) * 0.25


def glitch_sfx():
    """ザザッというノイズ (短く、途切れ途切れ)"""
    rng = np.random.default_rng(2)
    n = rng.normal(0, 1, int(SR * 0.35))
    gate = np.repeat(rng.random(len(n) // 600 + 1) > 0.35, 600)[: len(n)]
    return n * gate * np.linspace(1, 0.2, len(n)) * 0.6


def drone(total):
    """不穏な持続音 (BGM の代わり)。低い音を 2 つ少しずらして重ね、ゆっくり揺らす。高い音がうっすら鳴る"""
    t = np.arange(int(SR * total)) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    low = (np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 55.6 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t)) * lfo
    high = 0.18 * np.sin(2 * np.pi * 659 * t + 2 * np.sin(2 * np.pi * 0.3 * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
    return (low + high) * np.minimum(1, t / 2.0) * np.minimum(1, (total - t) / 1.5)


# ---- サムネイル (1280x720) -------------------------------------------------------
def duotone(im, gamma_r=1.1, gamma_gb=3.0):
    """白黒にしてから赤黒く染める。暗いところは赤黒く、明るいところ (仮面) だけ白く残る"""
    g = ImageEnhance.Contrast(ImageEnhance.Brightness(im.convert("L")).enhance(0.85)).enhance(1.5)
    lut_r = [int(255 * (v / 255) ** gamma_r) for v in range(256)]
    lut_gb = [int(255 * (v / 255) ** gamma_gb) for v in range(256)]
    return Image.merge("RGB", (g.point(lut_r), g.point(lut_gb), g.point(lut_gb))).convert("RGBA")


def side_panel(name, scale, cx, cy, pw, side):
    """写真の (cx, cy) を中心に、幅 pw・高さ 720 を切り出して赤黒くし、内側 (中央側) へ闇に溶かす"""
    TH = 720
    im = load(name)
    s = TH / im.height * scale
    big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0 = int(min(max(big.width * cx - pw / 2, 0), big.width - pw))
    y0 = int(min(max(big.height * cy - TH / 2, 0), big.height - TH))
    p = duotone(big.crop((x0, y0, x0 + pw, y0 + TH)))
    fade = Image.linear_gradient("L").rotate(90, expand=True).resize((pw, TH))   # 左が黒 → 右が白
    if side == "left":
        fade = fade.transpose(Image.FLIP_LEFT_RIGHT)                         # 左パネルは右 (中央側) を消す
    fade = fade.point(lambda v: min(255, int(v * 1.6)))
    p.putalpha(fade)
    return p


def thumbnail(path):
    """都市伝説チャンネル風: 真ん中に赤黒いカオナシ、左右に赤い巨大な 2 文字「正」「体」、
    上下に横幅いっぱいの太い明朝 (黄色＋黒フチ)。「現代人」だけ赤"""
    TW, TH = 1280, 720
    rng = random.Random(4)
    YEL = (255, 222, 0)
    im = load("chihiro/033")                    # 巨大化して襲いかかるカオナシ
    s = TH / im.height * 1.3
    big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x0, y0 = int(big.width * 0.56 - TW * 0.5), int(big.height * 0.37 - TH * 0.45)
    th = duotone(big.crop((x0, y0, x0 + TW, y0 + TH)))
    halo = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))   # 仮面のまわりを赤く光らせる
    ImageDraw.Draw(halo).ellipse((TW / 2 - 200, 60, TW / 2 + 200, 560), fill=(200, 0, 0, 100))
    th.alpha_composite(halo.filter(ImageFilter.GaussianBlur(80)))
    v = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))      # 周りと上下を暗く (文字を読みやすく)
    vd = ImageDraw.Draw(v)
    vd.rectangle((0, 0, TW, TH), outline=(0, 0, 0, 220), width=120)
    vd.rectangle((0, 0, TW, 130), fill=(0, 0, 0, 170))
    vd.rectangle((0, TH - 200, TW, TH), fill=(0, 0, 0, 190))
    th.alpha_composite(v.filter(ImageFilter.GaussianBlur(45)))
    n = np.random.default_rng(5).normal(128, 45, (TH, TW)).clip(0, 255).astype(np.uint8)   # ざらつき
    gr = Image.new("RGBA", (TW, TH), (255, 255, 255, 0))
    gr.putalpha(Image.eval(Image.fromarray(n, "L"), lambda p: abs(p - 128) // 5))
    th.alpha_composite(gr)

    def fit(el, width):
        k = min(1.0, width / el.width)
        return el.resize((round(el.width * k), round(el.height * k)), Image.LANCZOS)

    def worn(el, seed, amount):
        """インクのかすれ: ぼかしたノイズで、文字の中にまだらな薄い抜けを作る"""
        rng2 = np.random.default_rng(seed)
        coarse = Image.fromarray((rng2.random((el.height // 6 + 2, el.width // 6 + 2)) * 255).astype(np.uint8))
        coarse = np.array(coarse.resize(el.size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
        fine = rng2.random((el.height, el.width))
        a = np.array(el.getchannel("A"), dtype=np.float32)
        hole = (coarse < amount * 2.2) & (fine < 0.75)
        a *= np.where(hole, 0.35, 1.0)
        out = el.copy()
        out.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
        return out

    def double(text, size, fill, inner, outer, sw_in, sw_out, path=ANTIQUE, glow=None, seed=0, wear=0.06):
        """二重フチの文字 (内側のフチ＋外側の太い黒フチ)。中身はかすれさせ、後ろを赤くにじませる"""
        o = text_el(text, size, fill=outer, stroke=outer, sw=sw_out, path=path, glow=glow)
        i = worn(text_el(text, size, fill=fill, stroke=inner, sw=sw_in, path=path), seed, wear)
        el = Image.new("RGBA", o.size, (0, 0, 0, 0))
        el.alpha_composite(o)
        el.alpha_composite(i, (sw_out - sw_in, sw_out - sw_in))
        return el

    # 左右の巨大な赤い 2 文字
    for ch, cx in (("正", 205), ("体", TW - 205)):
        el = double(ch, 360, (215, 15, 25), (255, 255, 255), (0, 0, 0), 5, 16, path=BRUSH, glow=(150, 0, 0),
                    seed=ord(ch), wear=0.08)
        place(th, el, cx, TH / 2 + 10)
    # 上: 千と千尋に隠された真実 (黄色、横幅いっぱい)
    top = fit(double("千と千尋に隠された恐怖の真実", 92, YEL, (0, 0, 0), (0, 0, 0), 9, 9, seed=1), TW - 40)
    th.alpha_composite(top, ((TW - top.width) // 2, -6))
    # 下: カオナシは現代人だった (「現代人」だけ赤に白フチ)
    parts = [double("カオナシは", 124, YEL, (0, 0, 0), (0, 0, 0), 11, 11, seed=2),
             double("現代人", 150, (225, 20, 30), (255, 255, 255), (0, 0, 0), 6, 17, glow=(150, 0, 0), seed=3),
             double("だった", 124, YEL, (0, 0, 0), (0, 0, 0), 11, 11, seed=4)]
    row = Image.new("RGBA", (sum(p.width for p in parts) - 58 * 2, max(p.height for p in parts)), (0, 0, 0, 0))
    x = 0
    for p in parts:
        row.alpha_composite(p, (x, row.height - p.height - (8 if p is not parts[1] else 0)))
        x += p.width - 58
    row = fit(row, TW - 30)
    th.alpha_composite(row, ((TW - row.width) // 2, TH - row.height + 12))
    th.convert("RGB").save(path, quality=95)


# ---- 組み立て ---------------------------------------------------------------
def main(script=None, out_name="kaonashi_sample.mp4", make_thumb=True):
    """script を渡すと、その台本で作る (本編は kaonashi_full.py から呼ぶ)"""
    global SCRIPT
    if script is not None:
        SCRIPT = script
    OUT.mkdir(exist_ok=True)
    if make_thumb:
        thumbnail(OUT / "kaonashi_thumbnail.jpg")
    segs, t, chapter, chapter_t = [], 0.4, None, 0.0
    for i, s in enumerate(SCRIPT):
        a, kana = synth(s.get("say", s["sub"].replace("|", "")))
        if "chapter" in s:
            chapter, chapter_t = s["chapter"], t
        dur = len(a) / SR + (0.5 if s["img"] in ("title", "chapter") else GAP)
        segs.append(dict(i=i, start=t, dur=dur, voice=a, kana=kana, chapter=chapter, chapter_t=chapter_t))
        t += dur
    total = t + 1.2
    buf = np.zeros(int(SR * total) + SR)
    voice = np.zeros_like(buf)
    for sg in segs:
        a0 = int(sg["start"] * SR)
        voice[a0:a0 + len(sg["voice"])] += sg["voice"]
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    ref = active_rms(voice)
    dr = drone(total)
    buf[: len(dr)] += dr / np.sqrt(np.mean(dr ** 2)) * ref * 10 ** (-17 / 20)
    for sg in segs:
        name = SCRIPT[sg["i"]].get("sfx")
        if name:
            c = boom() if name == "boom" else glitch_sfx()
            a0 = int(sg["start"] * SR)
            gain = ref * 10 ** ((-6 if name == "boom" else -12) / 20) / active_rms(c)
            buf[a0:a0 + len(c)] += (c * gain)[: len(buf) - a0]
    wav = OUT / "_kaonashi_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(wav)
    out = OUT / out_name
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(round(total * FPS)):
        tt = f / FPS
        sg = dict(next((g for g in reversed(segs) if g["start"] <= tt), segs[0]), t=tt)
        frame = draw(sg, max(tt - sg["start"], 0), f)
        if tt < 0.5:                            # 暗闇から始まり、暗闇で終わる
            frame = Image.blend(Image.new("RGB", (W, H)), frame, tt / 0.5)
        if tt > total - 0.8:
            frame = Image.blend(frame, Image.new("RGB", (W, H)), min(1, (tt - (total - 0.8)) / 0.7))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(total=round(total, 2), lines=[(round(g["start"], 2), SCRIPT[g["i"]]["sub"], g["kana"]) for g in segs])
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
