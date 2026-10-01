"""ショート動画で定番の効果音を合成する（素材のライセンスを気にしなくていいように、全部 numpy で作る）。

whoosh: 場面転換の「シュッ」/ pop: テロップが出る「ポンッ」/ impact: 冒頭の「ドンッ」/ chime: 締めの「キラーン」
"""
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def bandpass_sweep(x, f0, f1):
    """1次の状態変数フィルタで中心周波数を f0→f1 に掃引する。"""
    n = len(x)
    fc = np.geomspace(f0, f1, n)
    f = 2 * np.sin(np.pi * fc / SR)
    q = 0.6
    lo = bp = 0.0
    out = np.empty(n)
    for i in range(n):
        hp = x[i] - lo - q * bp
        bp += f[i] * hp
        lo += f[i] * bp
        out[i] = bp
    return out


def whoosh():
    d = 0.42
    x = rng.standard_normal(len(t(d)))
    y = bandpass_sweep(x, 300, 4500)
    tt = t(d)
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2.2
    env *= np.exp(-((tt / d - 0.62) ** 2) / 0.08)
    return y * env


def pop():
    tt = t(0.14)
    f = 1100 * np.exp(-tt * 28) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt * 32) * np.minimum(tt * 2000, 1)


def impact():
    tt = t(0.9)
    f = 120 * np.exp(-tt * 9) + 42
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 4.5)
    click = rng.standard_normal(len(tt)) * np.exp(-tt * 60) * 0.5
    return np.tanh((body + click) * 1.8)


def chime():
    tt = t(1.6)
    y = np.zeros_like(tt)
    for k, (f, d) in enumerate([(1568, 0.0), (2093, 0.07), (2637, 0.14), (3136, 0.21)]):
        on = tt >= d
        u = tt - d
        y += on * (np.sin(2 * np.pi * f * u) + 0.3 * np.sin(2 * np.pi * f * 2.76 * u)) * np.exp(-u * 3.2)
    shimmer = bandpass_sweep(rng.standard_normal(len(tt)), 6000, 9000) * np.exp(-tt * 5) * 0.6
    return y + shimmer


def save(name, y, peak):
    y = y / np.max(np.abs(y)) * peak
    pcm = (y * 32767).astype("<i2")
    with wave.open(name, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


out = sys.argv[1] if len(sys.argv) > 1 else "build"
save(f"{out}/whoosh.wav", whoosh(), 0.9)
save(f"{out}/pop.wav", pop(), 0.9)
save(f"{out}/impact.wav", impact(), 0.95)
save(f"{out}/chime.wav", chime(), 0.8)
