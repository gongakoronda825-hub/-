"""ジブリ作品リング脱出レース (YouTube ショート / TikTok 向け)

画面の中央に回る 3 重のリング。6 作品のボールが跳ね回り、3 枚全部の隙間をくぐって最初に外へ出た子が 1 位。
2 位・3 位は、1 位が脱出した瞬間に何枚抜けていたか (同じなら外側にいる方) で決める。
結果は物理演算 (rings.py) のまま。SEED を変えると別のレースになる。
ボール・文字・音声の部品はマーブルレース (race-video/make.py) のものを使う。
使い方: python3 ring-video/make.py   (VOICEVOX Engine を localhost:50021 で起動しておく)
"""
import importlib.util
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rings  # noqa: E402

_spec = importlib.util.spec_from_file_location("race", HERE.parent / "race-video" / "make.py")
race = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(race)
from_race = ("RACERS", "font", "outlined", "ball_icon", "name_tag", "place", "pill", "ease_back", "confetti",
             "synth", "load_sfx", "tone", "active_rms", "FFMPEG", "OUT", "W", "H", "FPS", "SR")
globals().update({k: getattr(race, k) for k in from_race})

SEED = 207                  # 1 枚目シータ → 2 枚目トトロ → 脱出ナウシカ。脱出の瞬間、2 匹があと 1 枚
SLOW = 0.25
SLOW_BEFORE = 0.8
SLOW_AFTER = 0.2
AFTER_WIN = 2.6             # 脱出してから表彰台までの秒数 (物理演算の時間)
PODIUM = 3.6
RING_COLORS = [(80, 230, 255), (255, 90, 200), (255, 214, 60)]
N = len(RACERS)
CX, CY = rings.CX, rings.CY


# ---- 背景 (一度だけ描く) -------------------------------------------------------
def background():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        u = y / H
        c0, c1 = (18, 16, 52), (70, 30, 90)
        d.line([(0, y), (W, y)], fill=tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3)))
    bg = bg.convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((CX - 520, CY - 520, CX + 520, CY + 520), fill=(120, 80, 200, 90))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    rng = random.Random(5)
    stars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(160):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.choice([1.5, 2, 2.5, 3.5])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rng.randint(90, 230)))
    bg.alpha_composite(stars)
    return bg


# ---- 1 フレーム ----------------------------------------------------------------
class Renderer:
    def __init__(self, res):
        self.res = res
        self.frames = res["frames"]
        self.win = min(res["escape"], key=res["escape"].get)
        self.t_win = res["escape"][self.win]
        self.s0, self.s1 = self.t_win - SLOW_BEFORE, self.t_win + SLOW_AFTER
        self.race_end_s = self.t_win + AFTER_WIN
        self.race_end = self.v_of(self.race_end_s)
        self.bg = background()
        fw = self.frames[min(int(round(self.t_win * FPS)), len(self.frames) - 1)]
        self.final = self.ranking(fw, self.t_win)
        # リングを最初に抜けた子 (k 枚目) と、その時刻
        self.firsts = {}
        for t, i, L in res["passes"]:
            if L not in self.firsts and L < len(rings.RINGS):
                self.firsts[L] = (t, i)
        self.total = self.race_end + PODIUM

    def v_of(self, s):
        return race.Renderer.v_of(self, s)

    def s_of(self, v):
        return race.Renderer.s_of(self, v)

    def ranking(self, fr, s):
        def key(i):
            if i in self.res["escape"] and self.res["escape"][i] <= s:
                return (9, -self.res["escape"][i])
            x, y, _ = fr["balls"][i]
            return (fr["layers"][i], math.hypot(x - CX, y - CY))
        return sorted(range(N), key=key, reverse=True)

    def state(self, s):
        x = min(max(s * FPS, 0), len(self.frames) - 1.001)
        f = int(x)
        a = x - f
        f0, f1 = self.frames[f], self.frames[f + 1]
        lerp = lambda p, q: p + (q - p) * a  # noqa: E731
        balls = [(lerp(b0[0], b1[0]), lerp(b0[1], b1[1]), lerp(b0[2], b1[2])) for b0, b1 in zip(f0["balls"], f1["balls"])]
        ring_a = [lerp(r0, r1) for r0, r1 in zip(f0["rings"], f1["rings"])]
        return dict(t=s, balls=balls, rings=ring_a, layers=f0["layers"])

    def draw_rings(self, frame, fr, s):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(core)
        for k, (R, ang) in enumerate(zip(rings.RINGS, fr["rings"])):
            # 誰かが抜けた直後は、そのリングを白く光らせる
            flash = max([1 - (s - t) / 0.35 for t, _, L in self.res["passes"] if L == k + 1 and 0 <= s - t < 0.35] + [0])
            col = tuple(int(c + (255 - c) * flash) for c in RING_COLORS[k])
            gap = rings.GAP / R
            a0, a1 = math.degrees(ang + gap), math.degrees(ang + 2 * math.pi)
            box = (CX - R, CY - R, CX + R, CY + R)
            d.arc(box, a0, a1, fill=col + (150 + int(100 * flash),), width=rings.RING_W * 2 + 22)
            dc.arc(box, a0, a1, fill=col + (255,), width=rings.RING_W * 2)
            dc.arc((CX - R + 5, CY - R + 5, CX + R - 5, CY + R - 5), a0, a1, fill=(255, 255, 255, 200), width=4)
        frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14)))
        frame.alpha_composite(core)

    def draw_balls(self, frame, fr, s):
        d = ImageDraw.Draw(frame)
        for i, (x, y, ang) in enumerate(fr["balls"]):     # 残像
            col = RACERS[i][6]
            for k in range(1, 6):
                ps = s - k * 0.03
                if ps < 0:
                    break
                px, py, _ = self.state(ps)["balls"][i]
                r = rings.BALL_R * (1 - k * 0.14)
                d.ellipse((px - r, py - r, px + r, py + r), fill=col + (int(110 - k * 20),))
        for i, (x, y, ang) in enumerate(fr["balls"]):
            if -80 < y < H + 80:
                place(frame, ball_icon(i, rings.BALL_R * 2), x, y, angle=-math.degrees(ang))
                place(frame, name_tag(i), x, y - rings.BALL_R - 24, scale=0.85)

    def board(self, order, fr, s):
        """下の順位表: 横に 6 つ並べ、各ボールの「あと何枚」"""
        im = Image.new("RGBA", (W - 40, 230), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=30, fill=(0, 0, 0, 130))
        d = ImageDraw.Draw(im)
        cw = im.width / N
        for rank, i in enumerate(order, 1):
            x = cw * (rank - 0.5)
            medal = {1: (255, 200, 0), 2: (200, 205, 215), 3: (205, 130, 70)}.get(rank, (110, 110, 110))
            d.ellipse((x - 22, 8, x + 22, 52), fill=medal + (255,))
            d.text((x, 31), str(rank), font=font(30), fill="black", anchor="mm")
            im.alpha_composite(ball_icon(i, 96), (int(x - 48), 60))
            escaped = i in self.res["escape"] and self.res["escape"][i] <= s
            left = len(rings.RINGS) - min(fr["layers"][i], len(rings.RINGS))
            label, col = ("脱出！", (255, 214, 0)) if escaped else \
                (("脱出寸前", (255, 120, 120)) if left == 0 else (f"あと{left}枚", (255, 255, 255)))
            d.text((x, 190), label, font=font(32), fill=col, anchor="mm", stroke_width=4, stroke_fill="black")
        return im

    def race_frame(self, v):
        s = self.s_of(v)
        fr = self.state(s)
        frame = self.bg.copy()
        self.draw_rings(frame, fr, s)
        self.draw_balls(frame, fr, s)
        order = self.ranking(fr, s) if s < self.t_win else self.final
        frame.alpha_composite(self.board(order, fr, s), (20, 1640))

        # タイトル (ずっと上に出しておく)
        place(frame, pill(outlined("リングから最初に", 66), (150, 20, 20), alpha=235), W / 2, 200,
              scale=min(1, 0.7 + 0.3 * ease_back(v / 0.3)))
        place(frame, pill(outlined("脱出するのはどれ？", 66, fill=(255, 214, 0)), (150, 20, 20), alpha=235), W / 2, 315,
              scale=min(1, 0.7 + 0.3 * ease_back((v - 0.1) / 0.3)))
        if v < 3.0:
            place(frame, outlined("コメントで予想してね👇", 50), W / 2, 430, alpha=min(1, v * 4, (3.0 - v) * 4))
        # k 枚目を最初に突破した子のお知らせ
        for L, (t, i) in self.firsts.items():
            if t <= s < t + 1.6 and s < self.s0:
                el = s - t
                el_txt = f"{RACERS[i][1]}が {L}枚目を一番乗り！"
                place(frame, pill(outlined(el_txt, 48), RACERS[i][6], alpha=235), W / 2, 450,
                      scale=ease_back(el / 0.25), alpha=min(1, (1.6 - el) * 4))
        # スロー
        if self.s0 <= s < self.s1:
            el = v - self.s0
            vg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(vg).rectangle((0, 0, W, H), outline=(0, 0, 0, 120), width=90)
            frame.alpha_composite(vg.filter(ImageFilter.GaussianBlur(50)))
            if s < self.t_win:
                place(frame, pill(outlined(f"{RACERS[self.win][1]}、脱出なるか…!?", 56), (30, 30, 30), alpha=220),
                      W / 2, 450, scale=0.7 + 0.3 * ease_back(el / 0.25))
            if int(el * 2) % 2 == 0:
                place(frame, outlined("スロー再生", 44, fill=(255, 80, 80)), W - 160, 70)
        # 脱出成功
        if s >= self.t_win:
            vw = self.v_of(self.t_win)
            el = v - vw
            confetti(frame, vw, v)
            p = ease_back(el / 0.3)
            place(frame, outlined("脱出成功！", 110, fill=(255, 214, 0)), W / 2, 470, scale=p)
            place(frame, pill(outlined(f"1位は『{RACERS[self.win][0]}』！", 54), (200, 150, 0), alpha=240),
                  W / 2, 1530, scale=ease_back((el - 0.25) / 0.3))
        return frame

    def podium_frame(self, v):
        frame = self.bg.copy()
        el = v - self.race_end
        d = ImageDraw.Draw(frame)
        place(frame, outlined("レース結果", 96), W / 2, 330)
        spots = [(1, W / 2, 1050, 300), (2, W / 2 - 300, 1180, 240), (3, W / 2 + 300 - 50, 1260, 220)]
        fw = self.state(self.t_win)
        for rank, x, y, size in spots:
            i = self.final[rank - 1]
            p = ease_back((el - 0.15 * (3 - rank)) / 0.35)
            col = {1: (255, 200, 0), 2: (200, 205, 215), 3: (205, 130, 70)}[rank]
            top = y + size / 2 + 20
            d.rectangle((x - size / 2 - 10, top, x + size / 2 + 10, 1560), fill=col + (255,), outline=(60, 60, 60, 255), width=6)
            d.text((x, top + 70), str(rank), font=font(110), fill="white", anchor="mm", stroke_width=8, stroke_fill="black")
            place(frame, ball_icon(i, size), x, y, scale=p)
            place(frame, outlined(RACERS[i][0], 40 if rank == 1 else 32), x, y - size / 2 - 40, alpha=min(1, p))
            left = len(rings.RINGS) - min(fw["layers"][i], len(rings.RINGS))
            note = "脱出！" if rank == 1 else f"あと{left}枚"
            d.text((x, top + 170), note, font=font(40), fill="white", anchor="mm", stroke_width=5, stroke_fill="black")
        place(frame, outlined("予想は当たった？コメントで教えてね💬", 52), W / 2, 1700, alpha=min(1, el * 3))
        return frame

    def frame(self, v):
        fr = self.race_frame(v) if v < self.race_end else self.podium_frame(v)
        if self.race_end - 0.25 < v < self.race_end + 0.25:
            a = 1 - abs(v - self.race_end) / 0.25
            fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * a))))
        return fr.convert("RGB")


# ---- 音 -----------------------------------------------------------------------
def make_audio(r, voices, total):
    buf = np.zeros(int(SR * total) + SR)

    def add(clip, t, gain=1.0):
        a = int(t * SR)
        if 0 <= a < len(buf):
            buf[a:a + len(clip)] += clip[: len(buf) - a] * gain

    voice = np.zeros_like(buf)
    for t, clip in voices:
        a = int(t * SR)
        voice[a:a + len(clip)] += clip[: len(voice) - a]
    voice *= 10 ** (-13 / 20) / active_rms(voice)
    buf += voice
    ref = active_rms(voice)
    # ぶつかる音 (ボールごとに音の高さを変える)
    notes = [523, 587, 659, 784, 880, 1047]
    last = {}
    for t, i, imp in r.res["hits"]:
        if t >= r.race_end_s or t - last.get(i, -1) < 0.06:
            continue
        last[i] = t
        add(tone(notes[i], 0.12, 35), r.v_of(t), ref * 0.45 * min(1.0, imp / 1500))
    # リングを抜けた「キラーン」(上がる 2 音)
    for t, i, L in r.res["passes"]:
        if t < r.t_win - 0.01:
            add(tone(1047 * 2 ** ((L - 1) * 4 / 12), 0.12, 20), r.v_of(t), ref * 0.6)
            add(tone(1568 * 2 ** ((L - 1) * 4 / 12), 0.25, 12), r.v_of(t) + 0.08, ref * 0.6)
    target = ref * 10 ** (-12 / 20)
    tt = np.arange(int(SR * 0.7)) / SR
    sweep = np.sin(2 * np.pi * np.cumsum(1400 * np.exp(-tt * 3.5) + 150) / SR) * np.exp(-tt * 3)
    add(sweep, r.v_of(r.s0), ref * 0.7)
    for t, name in ((r.v_of(r.t_win), "jean1.mp3"), (r.race_end, "decision52.mp3")):
        c = load_sfx(name)
        add(c * target / active_rms(c), t)
    path = OUT / "_ring_mix.f32"
    buf[: int(SR * total)].astype("<f4").tofile(path)
    return path


def main():
    OUT.mkdir(exist_ok=True)
    res = rings.simulate(SEED, max_time=40, after=AFTER_WIN + 0.5)
    r = Renderer(res)
    v1, k1 = synth("最初にリングから脱出するのは、どの作品？", 1.3)
    v2, k2 = synth(f"脱出成功！1位は、{RACERS[r.win][0]}！", 1.3)
    v3, k3 = synth("予想は当たった？コメントで教えてね！", 1.3)
    voices = [(0.05, v1), (r.v_of(r.t_win) + 0.5, v2), (r.race_end + 0.3, v3)]
    total = max(r.race_end + 0.3 + len(v3) / SR + 0.5, voices[1][0] + len(v2) / SR + 0.3)
    r.total = total
    wav = make_audio(r, voices, total)
    out = OUT / "ghibli_ring_escape.mp4"
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,volume=3dB,alimiter=limit=0.89:level=false",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    if len(sys.argv) > 1:                       # プレビュー: 指定した秒のフレームだけ PNG に書き出す
        for t in sys.argv[1:]:
            r.frame(float(t)).save(OUT / f"_ring_{t}.png")
        wav.unlink()
        return
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(round(total * FPS)):
        proc.stdin.write(r.frame(i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    info = dict(seed=SEED, total=round(total, 2), winner=RACERS[r.win][0], t_win=round(r.t_win, 2),
                ranking=[RACERS[i][0] for i in r.final[:3]],
                firsts={L: RACERS[i][1] for L, (t, i) in r.firsts.items()}, kana=[k1, k2, k3])
    (OUT / "ghibli_ring_escape_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
