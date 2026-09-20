"""Pre-antialiased sprites + fast compositing onto a float32 canvas.

Every hard edge (bodies, eyes, rings) is generated once at 4x resolution and
box-downsampled, so blitting stays cheap while the edges stay smooth.
"""

from __future__ import annotations

import numpy as np

SS = 4  # supersampling factor used when baking the sprites


def _grid(size: int) -> tuple[np.ndarray, np.ndarray]:
    n = size * SS
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2.0
    return (x - c) / SS, (y - c) / SS


def _shrink(a: np.ndarray, size: int) -> np.ndarray:
    return a.reshape(size, SS, size, SS).mean(axis=(1, 3)).astype(np.float32)


def disc(radius: float, pad: float = 2.0) -> np.ndarray:
    size = int(np.ceil(radius * 2 + pad * 2))
    x, y = _grid(size)
    return _shrink((np.hypot(x, y) <= radius).astype(np.float32), size)


def ring(radius: float, width: float, pad: float = 2.0) -> np.ndarray:
    size = int(np.ceil((radius + width) * 2 + pad * 2))
    x, y = _grid(size)
    d = np.hypot(x, y)
    return _shrink(((d <= radius + width / 2) & (d >= radius - width / 2)).astype(np.float32), size)


def glow(radius: float, power: float = 2.4) -> np.ndarray:
    size = int(np.ceil(radius * 2 + 2))
    n = size
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2.0
    d = np.hypot(x - c, y - c) / radius
    return np.clip(1.0 - d, 0.0, 1.0) ** power


def blit(canvas: np.ndarray, alpha: np.ndarray, cx: float, cy: float,
         color, strength: float = 1.0, additive: bool = False) -> None:
    """Composite `alpha` (h, w) tinted with `color` centred on (cx, cy)."""
    if strength <= 0.002:
        return
    h, w = alpha.shape
    x0 = int(round(cx - w / 2.0))
    y0 = int(round(cy - h / 2.0))
    cw, ch = canvas.shape[1], canvas.shape[0]

    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(cw, x0 + w), min(ch, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return

    a = alpha[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0), None]
    if strength != 1.0:
        a = a * strength
    col = np.asarray(color, dtype=np.float32)
    dst = canvas[dy0:dy1, dx0:dx1]
    if additive:
        dst += a * col
    else:
        dst *= (1.0 - a)
        dst += a * col
