"""効果音を合成して 1本の音声トラック（WAV）にする。音楽は使わない。"""
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 21.0
rng = np.random.default_rng(7)


def t_(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def don(strength=1.0):
    """和太鼓のような低い「ドン」"""
    t = t_(1.6)
    f = 42 + 60 * np.exp(-t / 0.06)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 0.45)
    skin = lp(rng.standard_normal(len(t)), 900) * env(len(t), 0.001, 0.03) * 0.8
    sub = np.sin(2 * np.pi * 38 * t) * env(len(t), 0.01, 0.7) * 0.5
    return (body + skin + sub) * strength


def shu():
    """風を切る「シュッ」"""
    n = int(0.32 * SR)
    x = rng.standard_normal(n)
    x = bp(x, 1800, 7000)
    t = np.arange(n) / SR
    e = np.sin(np.pi * np.clip(t / 0.32, 0, 1)) ** 2.5
    return x * e * 0.45


def ton():
    """軽い拍子木のような「トン」"""
    t = t_(0.35)
    wood = (np.sin(2 * np.pi * 620 * t) + 0.5 * np.sin(2 * np.pi * 1340 * t)) * env(len(t), 0.001, 0.045)
    low = np.sin(2 * np.pi * 150 * t) * env(len(t), 0.002, 0.09)
    return (wood * 0.55 + low * 0.6)


def furin():
    """風鈴"""
    t = t_(2.2)
    parts = [(2350, 1.0, 0.9), (5760, 0.45, 0.5), (8900, 0.25, 0.3), (3120, 0.3, 0.7)]
    x = sum(a * np.sin(2 * np.pi * f * t) * env(len(t), 0.002, d) for f, a, d in parts)
    x += 0.4 * np.sin(2 * np.pi * 2350 * t) * env(len(t), 0.002, 0.9) * np.sin(2 * np.pi * 5 * t)
    return x * 0.22


def splash():
    """水しぶき「ザバーッ」"""
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    cutoff = 1200 + 5000 * np.exp(-t / 0.25)
    # 時間で変わるローパスは短いブロックごとに処理
    out = np.zeros(n)
    blk = 1024
    zi = None
    for i in range(0, n, blk):
        c = cutoff[i]
        sos = signal.butter(2, c, btype="low", fs=SR, output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[i : i + blk], zi = signal.sosfilt(sos, x[i : i + blk], zi=zi)
    bubbles = np.zeros(n)
    for _ in range(40):
        s = int(rng.uniform(0.05, 1.4) * SR)
        m = int(0.05 * SR)
        tt = np.arange(m) / SR
        f = rng.uniform(500, 1400)
        bubbles[s : s + m] += np.sin(2 * np.pi * (f + 3000 * tt) * tt) * np.exp(-tt / 0.012) * rng.uniform(0.1, 0.3)
    return (out * env(n, 0.04, 0.7) * 1.1 + bubbles) * 0.8


def wind(sec):
    """風が吹き抜ける音"""
    n = int(sec * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 250, 1600)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * t + 1.0)
    shape = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 1.5
    return x * mod * shape * 0.35


def drop():
    """水滴「ポチャン」"""
    t = t_(0.9)
    f = 700 + 1500 * (1 - np.exp(-t / 0.02))
    plink = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.07)
    t2 = t_(0.9)
    ring = np.sin(2 * np.pi * 1900 * t2) * env(len(t2), 0.03, 0.18) * 0.25
    return (plink + ring) * 0.7


def main(out_path):
    mix = np.zeros((int(DUR * SR), 2))

    def put(sound, at, gain=1.0, pan=0.0):
        s = int(at * SR)
        e = min(s + len(sound), len(mix))
        seg = sound[: e - s] * gain
        mix[s:e, 0] += seg * (1 - max(pan, 0))
        mix[s:e, 1] += seg * (1 + min(pan, 0))

    # 1 冒頭：0.0秒ちょうどに「ドン」
    put(don(1.25), 0.0)
    # 2 日本公演：東京で「シュッ」、4都市で「トン×4」
    put(shu(), 1.42, 1.0)
    for i, at in enumerate([3.05, 3.3, 3.55, 3.8]):
        put(ton(), at, 0.9, pan=[-0.3, 0.3, -0.3, 0.3][i])
    # 3 introduction：風鈴 → 1行ごとに「ドン」、最後だけ強く
    put(furin(), 5.0, 0.9)
    put(don(0.7), 5.6)
    put(don(0.8), 6.6)
    put(don(1.2), 7.6)
    # 4 舞台写真3枚：切り替えごとに「シュッ」＋軽い「ドン」
    for at in [9.45, 10.95, 12.45]:
        put(shu(), at - 0.05, 0.9)
        put(don(0.45), at + 0.05)
    # 5 ポスター全体：水しぶき ＋ 風
    put(splash(), 14.05, 1.0)
    put(wind(4.2), 14.2, 0.9)
    # 6 問いかけ → 最後に水滴
    put(ton(), 18.05, 0.6)
    put(drop(), 20.35, 1.0)

    peak = np.max(np.abs(mix))
    mix = mix / peak * 0.89
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1])
