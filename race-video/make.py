"""ジブリ作品マーブルレース (YouTube ショート / TikTok 向け)

6 作品の場面写真を丸く切り抜いたボールが、物理演算のコースを転がってゴールを目指す。
カメラは先頭 (ゴール後は残りの先頭) を追いかけ、左上に順位表、ゴールで「1位は○○！」、最後に表彰台。
結果は物理演算で決まる。SEED を変えると別のレースになる (course.py の leader_changes で盛り上がりを確認して選ぶ)。
使い方: python3 race-video/make.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import io
import json
import math
import random
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import course  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
OUT = ROOT / "output"
SFX_DIR = ROOT / "chihiro-video" / "sfx"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = ROOT / "ghibli-video" / "fonts" / "NotoSansJP.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS, SR = 1080, 1920, 30, 44100
SEED = 30                   # 先頭の入れ替わり 19 回・1 位と 2 位の差 0.23 秒の回
ENGINE = "http://localhost:50021"
SPEAKER = 2
PODIUM = 3.6                # 表彰台を見せる秒数

# (作品名, ボールの名前, 画像, 顔の中心 x, y, 切り抜く大きさ, 色)
RACERS = [
    ("千と千尋の神隠し", "千尋", "chihiro/050", 990, 450, 600, (232, 92, 92)),
    ("となりのトトロ", "トトロ", "totoro/030", 990, 450, 1000, (90, 160, 90)),
    ("天空の城ラピュタ", "シータ", "laputa/005", 840, 285, 520, (70, 130, 220)),
    ("風の谷のナウシカ", "ナウシカ", "nausicaa/010", 990, 372, 700, (240, 160, 40)),
    ("魔女の宅急便", "キキ", "majo/013", 900, 312, 560, (150, 90, 200)),
    ("もののけ姫", "サン", "mononoke/049", 1080, 522, 600, (200, 60, 60)),
]


# ---- 部品 ---------------------------------------------------------------------
_cache = {}


def font(size, weight=b"Black"):
    key = ("f", size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_name(weight)
        _cache[key] = f
    return _cache[key]


def emoji(ch, size):
    key = ("e", ch, size)
    if key not in _cache:
        e = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), ch, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True)
        e = e.crop(e.getbbox())
        _cache[key] = e.resize((size, round(size * e.height / e.width)), Image.LANCZOS)
    return _cache[key]


def outlined(text, size, fill="white", stroke="black"):
    f = font(size)
    sw = max(5, size // 8)
    body = "".join(ch for ch in text if ord(ch) < 0x1F000)
    emo = [ch for ch in text if ord(ch) >= 0x1F000]
    w = int(f.getlength(body)) + sw * 2 + (int(size * 1.1) + 8 if emo else 0)
    im = Image.new("RGBA", (w + 4, int(size * 1.4) + sw * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((sw, sw), body, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    if emo:
        im.alpha_composite(emoji(emo[0], int(size * 1.05)), (int(f.getlength(body)) + sw * 2 + 4, sw + int(size * 0.2)))
    return im


def ball_icon(i, d):
    """場面写真の顔を丸く切り抜き、白フチ＋チーム色の輪を付けたボール (直径 d)"""
    key = ("ball", i, d)
    if key not in _cache:
        _, _, img, cx, cy, size, color = RACERS[i]
        work, num = img.split("/")
        src = Image.open(RAW / work / f"{work}{num}.jpg").convert("RGB")
        face = src.crop((cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2)).resize((d * 4, d * 4), Image.LANCZOS)
        S = d * 4
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).ellipse((S * 0.09, S * 0.09, S * 0.91, S * 0.91), fill=255)
        dr = ImageDraw.Draw(im)
        dr.ellipse((0, 0, S - 1, S - 1), fill=color + (255,))
        dr.ellipse((S * 0.05, S * 0.05, S * 0.95, S * 0.95), fill=(255, 255, 255, 255))
        im.paste(face, (0, 0), mask)
        _cache[key] = im.resize((d, d), Image.LANCZOS)
    return _cache[key]


def name_tag(i):
    key = ("tag", i)
    if key not in _cache:
        color = RACERS[i][6]
        t = outlined(RACERS[i][1], 34)
        im = Image.new("RGBA", (t.width + 16, t.height), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 6, im.width - 1, im.height - 6), radius=16, fill=color + (230,))
        im.alpha_composite(t, (8, 0))
        _cache[key] = im
    return _cache[key]


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def place(frame, el, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        el = el.resize((max(1, round(el.width * scale)), max(1, round(el.height * scale))), Image.BICUBIC)
    if angle:
        el = el.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        el = el.copy()
        el.putalpha(el.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(el, (round(cx - el.width / 2), round(cy - el.height / 2)))


def pill(el, color, alpha=230, pad=(30, 8)):
    p = Image.new("RGBA", (el.width + pad[0] * 2, el.height + pad[1] * 2), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, p.height - 1), radius=30, fill=color + (alpha,))
    p.alpha_composite(el, pad)
    return p


# ---- コースの絵 (一度だけ描く) -------------------------------------------------
COURSE_H = course.FINISH_Y + 1100
TOP = -300                   # コース画像の y=0 が、ワールド座標の TOP


def course_image(segs):
    im = Image.new("RGBA", (W, COURSE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for a, b, r, kind in segs:
        if kind == "wall":
            p1, p2 = (a[0], a[1] - TOP), (b[0], b[1] - TOP)
            d.line([p1, p2], fill=(40, 70, 55, 255), width=int(r * 2 + 8))
            d.line([p1, p2], fill=(120, 190, 140, 255), width=int(r * 2 - 2))
            for p in (p1, p2):
                d.ellipse((p[0] - r - 4, p[1] - r - 4, p[0] + r + 4, p[1] + r + 4), fill=(40, 70, 55, 255))
        elif kind == "peg":
            x, y = a[0], a[1] - TOP
            d.ellipse((x - r - 3, y - r - 3, x + r + 3, y + r + 3), fill=(40, 70, 55, 255))
            d.ellipse((x - r + 3, y - r + 3, x + r - 3, y + r - 3), fill=(255, 230, 140, 255))
        elif kind == "bumper":
            x, y = a[0], a[1] - TOP
            d.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=(120, 30, 70, 255))
            d.ellipse((x - r + 4, y - r + 4, x + r - 4, y + r - 4), fill=(255, 120, 170, 255))
            d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=(255, 220, 235, 255))
    fy = course.FINISH_Y - TOP           # ゴールラインは市松模様
    for k in range(0, W, 40):
        for j in range(2):
            if (k // 40 + j) % 2 == 0:
                d.rectangle((k, fy + j * 20, k + 40, fy + j * 20 + 20), fill=(20, 20, 20, 255))
            else:
                d.rectangle((k, fy + j * 20, k + 40, fy + j * 20 + 20), fill=(255, 255, 255, 255))
    gt = outlined("GOAL", 90, fill=(255, 214, 0))
    im.alpha_composite(gt, ((W - gt.width) // 2, fy - gt.height - 10))
    return im


def background():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(205 + 40 * t), int(232 + 15 * t), int(245 - 20 * t)))
    return bg.convert("RGBA")


# ---- 1 フレーム ----------------------------------------------------------------
def standings(fr, finish, t):
    """順位: ゴール済みはゴール順、まだの子は進んだ距離 (y) の大きい順"""
    done = sorted([i for i, ft in finish.items() if ft <= t], key=lambda i: finish[i])
    rest = sorted([i for i in range(len(RACERS)) if i not in done], key=lambda i: -fr["balls"][i][1])
    return done + rest


def board(order):
    rows = []
    for rank, i in enumerate(order, 1):
        row = Image.new("RGBA", (330, 62), (0, 0, 0, 0))
        medal = {1: (255, 200, 0), 2: (200, 205, 215), 3: (205, 130, 70)}.get(rank, (90, 90, 90))
        d = ImageDraw.Draw(row)
        d.ellipse((2, 9, 46, 53), fill=medal + (255,))
        d.text((24, 31), str(rank), font=font(30), fill="black", anchor="mm")
        row.alpha_composite(ball_icon(i, 50), (54, 6))
        d.text((114, 31), RACERS[i][1], font=font(34), fill="white", anchor="lm", stroke_width=4, stroke_fill="black")
        rows.append(row)
    im = Image.new("RGBA", (350, 62 * len(rows) + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=24, fill=(0, 0, 0, 120))
    for k, r in enumerate(rows):
        im.alpha_composite(r, (10, 10 + 62 * k))
    return im


def confetti(frame, t0, t):
    rng = random.Random(7)
    el = t - t0
    if not 0 <= el < 2.5:
        return
    d = ImageDraw.Draw(frame)
    for _ in range(90):
        x0, vx, vy = rng.uniform(0, W), rng.uniform(-120, 120), rng.uniform(250, 600)
        c = rng.choice([(255, 90, 90), (255, 214, 0), (90, 200, 120), (90, 150, 255), (255, 140, 220)])
        x, y = x0 + vx * el, -40 + vy * el + 300 * el * el * 0.5
        s = 16
        d.rectangle((x, y, x + s, y + s * 0.6), fill=c + (255,))


class Renderer:
    def __init__(self, res, voices):
        self.res = res
        self.frames = res["frames"]
        self.finish = res["finish"]
        self.order_final = sorted(self.finish, key=lambda i: self.finish[i])
        self.t_win = self.finish[self.order_final[0]]
        self.t_third = self.finish[self.order_final[2]]
        self.race_end = self.t_third + 1.2
        self.total = self.race_end + PODIUM
        self.bg = background()
        self.course = course_image(res["segs"])
        self.cams = self._camera()
        self.voices = voices

    def _camera(self):
        cams, cam = [], -260.0
        for fr in self.frames:
            t = fr["t"]
            alive = [i for i in range(len(RACERS)) if self.finish.get(i, 1e9) > t - 0.6]
            ys = [fr["balls"][i][1] for i in (alive or range(len(RACERS)))]
            target = max(ys) - H * 0.45
            if t < course.GATE_OPEN:
                target = -260
            target = min(max(target, -260), course.FINISH_Y + 650 - H)
            cam += (target - cam) * 0.12
            cams.append(cam)
        return cams

    def race_frame(self, t):
        f = min(int(round(t * FPS)), len(self.frames) - 1)
        fr = self.frames[f]
        cam = self.cams[f]
        frame = self.bg.copy()
        y0 = int(cam - TOP)
        frame.alpha_composite(self.course.crop((0, y0, W, y0 + H)))
        d = ImageDraw.Draw(frame)
        for (mx, my, ma), (L, r) in zip(fr["movers"], self.res["movers"]):   # 回転する羽根
            dx, dy = L * math.cos(ma), L * math.sin(ma)
            p1, p2 = (mx - dx, my - dy - cam), (mx + dx, my + dy - cam)
            d.line([p1, p2], fill=(120, 40, 40, 255), width=r * 2 + 8)
            d.line([p1, p2], fill=(240, 120, 90, 255), width=r * 2 - 2)
            d.ellipse((mx - 18, my - cam - 18, mx + 18, my - cam + 18), fill=(80, 30, 30, 255))
        if t < course.GATE_OPEN:                                             # スタートの仕切り
            d.line([(300, 360 - cam), (780, 360 - cam)], fill=(200, 60, 60, 255), width=20)
        for i, (x, y, ang) in enumerate(fr["balls"]):
            sy = y - cam
            if -100 < sy < H + 100:
                place(frame, ball_icon(i, course.R * 2), x, sy, angle=-math.degrees(ang))
                place(frame, name_tag(i), x, sy - course.R - 26)
        order = standings(fr, self.finish, t)
        frame.alpha_composite(board(order), (24, 170))

        # 冒頭: 予想を呼びかけ → 3・2・1・スタート
        if t < course.GATE_OPEN + 0.8:
            a = min(1, t * 4)
            place(frame, pill(outlined("1位になるのはどれ？", 68), (150, 20, 20)), W / 2, 1020, alpha=a,
                  scale=0.7 + 0.3 * ease_back(t / 0.3))
            place(frame, outlined("コメントで予想してね👇", 54), W / 2, 1130, alpha=a)
            for k, lab in enumerate(["3", "2", "1", "スタート！"]):
                tk = course.GATE_OPEN - 1.8 + 0.6 * k
                if tk <= t < tk + 0.6 or (k == 3 and tk <= t < tk + 0.8):
                    size = 220 if k < 3 else 130
                    place(frame, outlined(lab, size, fill=(255, 214, 0)), W / 2, 1380,
                          scale=1.4 - 0.4 * ease_back((t - tk) / 0.2))
        # 1 位のゴール
        if t >= self.t_win:
            w = self.order_final[0]
            el = t - self.t_win
            confetti(frame, self.t_win, t)
            if el < 3.0:
                p = ease_back(el / 0.3)
                banner = pill(outlined(f"1位は『{RACERS[w][0]}』！", 60), (200, 150, 0), alpha=240)
                place(frame, banner, W / 2, 760, scale=0.6 + 0.4 * p)
                place(frame, ball_icon(w, 200), W / 2, 560, scale=p)
        return frame

    def podium_frame(self, t):
        frame = self.bg.copy()
        el = t - self.race_end
        d = ImageDraw.Draw(frame)
        place(frame, outlined("レース結果", 96), W / 2, 330)
        spots = [(1, W / 2, 1050, 300), (2, W / 2 - 300, 1180, 240), (3, W / 2 + 300 - 50, 1260, 220)]
        for k, (rank, x, y, size) in enumerate(spots):
            i = self.order_final[rank - 1]
            p = ease_back((el - 0.15 * (3 - rank)) / 0.35)
            col = {1: (255, 200, 0), 2: (200, 205, 215), 3: (205, 130, 70)}[rank]
            top = y + size / 2 + 20
            d.rectangle((x - size / 2 - 10, top, x + size / 2 + 10, 1560), fill=col + (255,), outline=(60, 60, 60, 255), width=6)
            d.text((x, top + 70), str(rank), font=font(110), fill="white", anchor="mm", stroke_width=8, stroke_fill="black")
            place(frame, ball_icon(i, size), x, y, scale=p)
            place(frame, outlined(RACERS[i][0], 40 if rank == 1 else 32), x, y - size / 2 - 40, alpha=min(1, p))
        place(frame, outlined("予想は当たった？コメントで教えてね💬", 52), W / 2, 1700, alpha=min(1, el * 3))
        return frame

    def frame(self, t):
        fr = self.race_frame(t) if t < self.race_end else self.podium_frame(t)
        if self.race_end - 0.25 < t < self.race_end + 0.25:      # 表彰台へは白くフェード
            a = 1 - abs(t - self.race_end) / 0.25
            fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * a))))
        return fr.convert("RGB")


# ---- 音 -----------------------------------------------------------------------
def post(path, params, body=b""):
    req = urllib.request.Request(f"{ENGINE}{path}?{urllib.parse.urlencode(params)}", data=body,
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def synth(text, speed=1.25):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            if m.get("consonant") and m["consonant_length"] < 0.045:
                m["consonant_length"] = 0.045
    q.update(speedScale=speed, pauseLengthScale=0.5, prePhonemeLength=0.0, postPhonemeLength=0.05,
             outputSamplingRate=SR, outputStereo=False)
    with wave.open(io.BytesIO(post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode()))) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return (a[idx[0]: idx[-1] + 1] if len(idx) else a), q["kana"]


def load_sfx(name):
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", str(SFX_DIR / name), "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 50):] if len(idx) else a


def tone(freq, dur, decay, amp=1.0):
    t = np.arange(int(SR * dur)) / SR
    return amp * (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)) * np.exp(-t * decay)


def active_rms(a):
    act = a[np.abs(a) > 0.02]
    return np.sqrt(np.mean(act ** 2)) if len(act) else 1e-9


def make_audio(r, total):
    buf = np.zeros(int(SR * total) + SR)

    def add(clip, t, gain=1.0):
        a = int(t * SR)
        if 0 <= a < len(buf):
            buf[a:a + len(clip)] += clip[: len(buf) - a] * gain

    # ナレーション
    voice = np.zeros_like(buf)
    for t, clip in r.voices:
        a = int(t * SR)
        voice[a:a + len(clip)] += clip[: len(voice) - a]
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    ref = active_rms(voice)
    # ぶつかる音: ボールごとに音の高さを変える (ペンタトニック)。画面の外は小さく
    notes = [523, 587, 659, 784, 880, 1047]
    last = {}
    for t, i, imp in r.res["hits"]:
        if t >= r.race_end or t - last.get(i, -1) < 0.07:
            continue
        last[i] = t
        f = min(int(t * FPS), len(r.frames) - 1)
        sy = r.frames[f]["balls"][i][1] - r.cams[f]
        g = min(1.0, imp / 1500) * (1.0 if 0 < sy < H else 0.25)
        add(tone(notes[i], 0.12, 35), t, ref * 0.5 * g)
    # 転がる「ゴロゴロ」: 画面に映っているボールの速さに合わせた低いノイズ。レース中の無音をなくす
    speeds = np.zeros(len(r.frames))
    for f in range(1, len(r.frames)):
        sp = 0.0
        for i in range(len(RACERS)):
            x0, y0, _ = r.frames[f - 1]["balls"][i]
            x1, y1, _ = r.frames[f]["balls"][i]
            if 0 < y1 - r.cams[f] < H and r.finish.get(i, 1e9) > r.frames[f]["t"]:
                sp += math.hypot(x1 - x0, y1 - y0) * FPS
        speeds[f] = sp
    env = np.clip(speeds / 2500, 0, 1) ** 0.7
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1, len(buf))
    rumble = np.zeros_like(noise)
    acc, k = 0.0, 0.035                           # 1 次のローパスで低い音だけにする
    for j in range(len(noise)):
        acc += k * (noise[j] - acc)
        rumble[j] = acc
    rumble /= np.max(np.abs(rumble)) + 1e-9
    t_axis = np.arange(len(buf)) / SR
    e = np.interp(t_axis, np.arange(len(env)) / FPS, env)
    e[(t_axis < course.GATE_OPEN) | (t_axis > r.race_end)] = 0
    buf += rumble * e * ref * 0.6

    # カウントダウン
    for k in range(3):
        add(tone(880, 0.15, 18), course.GATE_OPEN - 1.8 + 0.6 * k, ref * 0.9)
    add(tone(1760, 0.4, 8), course.GATE_OPEN, ref * 0.9)
    target = ref * 10 ** (-12 / 20)
    for t, name in ((r.t_win, "jean1.mp3"), (r.race_end, "decision52.mp3")):
        c = load_sfx(name)
        add(c * target / active_rms(c), t)
    path = OUT / "_race_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(path)
    return path


def main():
    OUT.mkdir(exist_ok=True)
    res = course.simulate(SEED)
    order = sorted(res["finish"], key=lambda i: res["finish"][i])
    win = order[0]
    v1, k1 = synth("1位になるのは、どの作品？", 1.3)
    v2, k2 = synth(f"1位は、{RACERS[win][0]}！", 1.3)
    v3, k3 = synth("予想は当たった？コメントで教えてね！", 1.3)
    r = Renderer(res, [])
    r.voices = [(0.05, v1), (r.t_win + 0.25, v2), (r.race_end + 0.3, v3)]
    r.total = r.race_end + 0.3 + len(v3) / 44100 + 0.5     # 表彰台は締めのナレーションが終わったらすぐ終わる
    total = r.total
    wav = make_audio(r, total)
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,volume=3dB,alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart",
           str(OUT / "ghibli_marble_race.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(round(total * FPS)):
        proc.stdin.write(r.frame(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(seed=SEED, total=round(total, 2), winner=RACERS[win][0],
                order=[(RACERS[i][0], round(res["finish"][i], 2)) for i in order],
                leader_changes=course.leader_changes(res), kana=[k1, k2, k3])
    (OUT / "ghibli_marble_race_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
