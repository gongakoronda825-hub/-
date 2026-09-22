"""冒頭のフックに乗せる効果音を合成する。

音源ファイルは使わず、その場で作る。使うのは2種類だけ。

- whoosh: ノイズにフィルタを掃かせた「シュッ」。目を引く合図と場面の切り替えに。
- bell:   倍音を非整数比で重ねた鈴の一撃。禅の主題に合い、声の邪魔もしない。

声より充分に小さく混ぜ、最後に全体をまとめてピークにそろえる。
"""

import numpy as np

WHOOSH_GAIN = 0.22
BELL_GAIN = 0.30


def _one_pole(signal, alpha):
    """1次ローパス。alphaは定数でも、サンプルごとに動く配列でもよい。"""
    coefficients = np.broadcast_to(np.asarray(alpha, dtype=float), signal.shape)
    out = np.empty_like(signal)
    y = 0.0
    for i in range(signal.size):
        y += coefficients[i] * (signal[i] - y)
        out[i] = y
    return out


def _cutoff_to_alpha(cutoff, rate):
    return 1.0 - np.exp(-2.0 * np.pi * cutoff / rate)


def whoosh(rate, duration=0.30, low=400.0, peak=5200.0, seed=7):
    """ノイズのカットオフを上げて下げる、短い「シュッ」。"""
    n = int(rate * duration)
    t = np.linspace(0.0, 1.0, n, endpoint=False)
    noise = np.random.default_rng(seed).standard_normal(n)

    # カットオフを山なりに動かす。上がりは速く、下がりはゆっくり。
    sweep = np.where(t < 0.45, t / 0.45, 1.0 - (t - 0.45) / 0.55 * 0.85)
    cutoff = low + (peak - low) * sweep ** 1.5
    body = _one_pole(noise, _cutoff_to_alpha(cutoff, rate))
    body -= _one_pole(body, _cutoff_to_alpha(180.0, rate))  # 低域の濁りを抜く

    envelope = np.sin(np.pi * t) ** 1.6
    body *= envelope
    return body / (np.max(np.abs(body)) or 1.0)


def bell(rate, duration=2.4, f0=1174.7, seed=11):
    """鈴（りん）の一撃。倍音を非整数比で重ね、高い倍音ほど早く減衰させる。"""
    n = int(rate * duration)
    t = np.arange(n) / rate
    partials = [(1.00, 1.00), (2.76, 0.52), (5.38, 0.28), (8.93, 0.16), (13.3, 0.08)]

    tone = np.zeros(n)
    for ratio, level in partials:
        decay = np.exp(-t / (1.9 / (1.0 + 0.55 * (ratio - 1.0))))
        # わずかに離調させた2本で、実物のようなうなりを出す。
        tone += level * decay * (np.sin(2 * np.pi * f0 * ratio * t)
                                 + 0.7 * np.sin(2 * np.pi * f0 * ratio * 1.003 * t))

    # 撞いた瞬間の「カッ」。8msだけノイズを混ぜる。
    strike = int(rate * 0.008)
    hit = np.random.default_rng(seed).standard_normal(strike)
    hit *= np.exp(-np.linspace(0.0, 6.0, strike))
    tone[:strike] += hit * 0.9 * np.max(np.abs(tone))

    tone *= np.minimum(t / 0.002, 1.0)  # 頭のプツッを消す
    return tone / (np.max(np.abs(tone)) or 1.0)


def hook_cues(rate, hand_off):
    """(開始秒, 波形) の並び。hand_offはフックから字幕に切り替わる時刻。"""
    return [
        (0.00, whoosh(rate) * WHOOSH_GAIN),
        (0.12, bell(rate) * BELL_GAIN),
        (max(0.0, hand_off - 0.08), whoosh(rate, duration=0.22, peak=4200.0,
                                           seed=3) * WHOOSH_GAIN * 0.8),
    ]


def mix(pcm, rate, cues, target_peak_dbfs):
    """int16のPCMに効果音を重ね、全体をtarget_peak_dbfsにそろえて返す。"""
    track = np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0
    for at, wave in cues:
        start = int(at * rate)
        end = min(start + wave.size, track.size)
        if end > start:
            track[start:end] += wave[:end - start]

    peak = np.max(np.abs(track)) or 1.0
    track *= 10.0 ** (target_peak_dbfs / 20.0) / peak
    return np.round(track * 32767.0).astype("<i2").tobytes()
