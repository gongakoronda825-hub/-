"""Palette and the speed -> colour mapping that carries the whole idea."""

from __future__ import annotations

import numpy as np

# slow ------------------------------------------------------------> fast
_STOPS = [
    (0.00, (48, 96, 255)),    # blue
    (0.18, (0, 190, 240)),    # cyan
    (0.38, (60, 230, 140)),   # green
    (0.55, (225, 230, 60)),   # yellow
    (0.75, (255, 140, 45)),   # orange
    (1.00, (255, 55, 65)),    # red
]

_LUT_N = 512


def _build_lut() -> np.ndarray:
    xs = np.array([s for s, _ in _STOPS])
    cs = np.array([c for _, c in _STOPS], dtype=np.float64)
    t = np.linspace(0.0, 1.0, _LUT_N)
    return np.stack([np.interp(t, xs, cs[:, i]) for i in range(3)], axis=1).astype(np.float32)


LUT = _build_lut()


def speed_color(s: float | np.ndarray) -> np.ndarray:
    """Map speed in [0, 1] to an RGB triple (or an (n, 3) array)."""
    idx = np.clip(np.asarray(s) * (_LUT_N - 1), 0, _LUT_N - 1).astype(np.int32)
    return LUT[idx]


# --- UI palette -----------------------------------------------------------
BG_DEEP = (7, 9, 16)
BG_GLOW = (20, 25, 44)
FIELD_EDGE = (58, 70, 104)
INK = (238, 243, 255)
INK_DIM = (150, 163, 194)
FOOD = (255, 243, 190)
DEAD = (74, 80, 96)
