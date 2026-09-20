"""Generated soundtrack — no samples, just numpy.

The pitch of every feeding blip is the eater's own speed, so as the population
evolves the sparkle climbs the scale along with the colours.  A slow pad tracks
the population mean underneath, and each generation change gets a soft thump.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
# A minor pentatonic across three octaves: slow creatures land low, fast high.
_SEMIS = np.array([0, 3, 5, 7, 10])
LADDER = np.concatenate([220.0 * 2.0 ** ((_SEMIS + 12 * o) / 12.0) for o in range(3)])


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    a = max(1, int(attack * SR))
    e = np.exp(-np.arange(n) / max(1.0, decay * SR))
    e[:a] *= np.linspace(0.0, 1.0, a)
    return e


def _add(buf: np.ndarray, at: int, seg: np.ndarray) -> None:
    if at >= len(buf):
        return
    n = min(len(seg), len(buf) - at)
    if n > 0:
        buf[at:at + n] += seg[:n]


def _blip(freq: float, dur: float = 0.16) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.32 * np.sin(4 * np.pi * freq * t)
    return (tone * _env(n, 0.002, 0.035)).astype(np.float32)


def _thump(freq: float = 82.0, dur: float = 0.34) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sweep = freq * np.exp(-t * 7.0) + 38.0
    body = np.sin(2 * np.pi * np.cumsum(sweep) / SR)
    click = np.random.default_rng(0).normal(0, 1, n) * np.exp(-t * 180.0) * 0.22
    return ((body + click) * _env(n, 0.001, 0.07)).astype(np.float32)


def _chord(freqs, dur: float, detune: float = 0.004) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float64)
    for i, f in enumerate(freqs):
        for d in (1.0 - detune, 1.0 + detune):
            out += np.sin(2 * np.pi * f * d * t + i) / (i + 2)
    return (out * _env(n, 0.02, dur * 0.55)).astype(np.float32)


def build_track(history, sched, fps: int, path: Path) -> Path:
    rng = np.random.default_rng(12345)
    total = int(sched.total / fps * SR) + SR // 2
    buf = np.zeros(total, dtype=np.float32)

    # --- pad that follows the population mean --------------------------------
    t = np.arange(total) / SR
    mean_by_frame = np.empty(sched.total, dtype=np.float64)
    for s in sched.slots:
        mean_by_frame[s.start:s.end] = history[s.gen].mean
    mean_by_frame[sched.gens_end:] = history[-1].mean
    mean_t = np.interp(np.clip(t * fps, 0, sched.total - 1),
                       np.arange(sched.total), mean_by_frame)
    base = 55.0 * 2.0 ** (mean_t * 0.9)
    phase = 2 * np.pi * np.cumsum(base) / SR
    pad = (np.sin(phase) + 0.45 * np.sin(2 * phase) + 0.2 * np.sin(3 * phase)) / 1.65
    swell = np.clip(np.minimum(t / 2.0, (total / SR - t) / 1.5), 0.0, 1.0)
    buf += (pad * swell * 0.055).astype(np.float32)

    # --- feeding blips, throttled so they stay a sparkle, not a buzz ---------
    last = -1.0
    for s in sched.slots:
        g = history[s.gen]
        shown = max(1, s.steps)
        eaten = g.food_eaten_step
        idx = np.flatnonzero((eaten >= 0) & (eaten <= shown))
        order = idx[np.argsort(eaten[idx])]
        for i in order:
            when = (s.start + eaten[i] / shown * s.forage) / fps
            if when - last < 0.055:
                continue
            last = when
            sp = float(g.speeds[g.food_eater[i]]) if g.food_eater[i] >= 0 else g.mean
            note = LADDER[int(np.clip(sp * (len(LADDER) - 1), 0, len(LADDER) - 1))]
            note *= 2.0 ** (rng.normal(0, 0.006))
            _add(buf, int(when * SR), _blip(note) * 0.085)

    # --- generation changes --------------------------------------------------
    for s in sched.slots[1:]:
        _add(buf, int(s.start / fps * SR), _thump() * 0.30)

    # --- the turn into the outro, then the landing ---------------------------
    out_at = sched.gens_end / fps
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    whoosh = rng.normal(0, 1, n) * np.exp(-((tt - 0.28) / 0.16) ** 2)
    whoosh *= np.linspace(0.3, 1.0, n)
    _add(buf, int((out_at - 0.35) * SR), (whoosh * 0.11).astype(np.float32))
    _add(buf, int(out_at * SR), _thump(120.0, 0.5) * 0.34)

    final = float(history[-1].mean)
    root = 110.0 * 2.0 ** (final * 0.9)
    _add(buf, int((out_at + 2.4) * SR), _chord([root, root * 1.5, root * 2.0], 1.6) * 0.10)
    _add(buf, int((out_at + 5.2) * SR),
         _chord([root, root * 1.25, root * 1.5, root * 2.0], 4.0) * 0.13)

    buf = np.tanh(buf * 1.35) * 0.82
    peak = float(np.abs(buf).max()) or 1.0
    buf = buf / peak * 0.90

    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path
