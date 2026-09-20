"""Cached font loading + text helpers drawn onto a per-frame RGBA overlay."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .layout import FONT_PATH, FONT_INDEX, W, H

_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    size = int(size)
    f = _CACHE.get(size)
    if f is None:
        f = ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
        _CACHE[size] = f
    return f


class Overlay:
    """One transparent text layer per frame, composited in a single pass."""

    def __init__(self):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def text(self, xy, s, size, color=(255, 255, 255), alpha=1.0,
             anchor="mm", shadow=0.0, stroke=0):
        if alpha <= 0.004 or not s:
            return
        a = int(max(0, min(255, round(alpha * 255))))
        f = font(size)
        if shadow > 0:
            sa = int(a * shadow)
            self.d.text((xy[0], xy[1] + max(2, size * 0.06)), s, font=f, anchor=anchor,
                        fill=(0, 0, 0, sa))
        kw = {}
        if stroke:
            kw = dict(stroke_width=stroke, stroke_fill=(6, 8, 14, a))
        self.d.text(xy, s, font=f, anchor=anchor, fill=(*color, a), **kw)

    def measure(self, s, size) -> tuple[int, int]:
        box = font(size).getbbox(s)
        return box[2] - box[0], box[3] - box[1]
