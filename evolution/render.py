"""Frame compositor.

Bodies, glows and rings are pre-antialiased sprites (baked at 4x, see
sprites.py) blitted onto a float32 canvas; text goes on a single RGBA overlay
per frame.  Nothing is drawn twice, so a frame costs a few tens of ms.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from . import colors as C
from . import sprites as S
from .layout import *  # noqa: F403  (pure constants)
from .sim import HIST_BINS, Generation, Params
from .timeline import Schedule
from .typography import Overlay, font

BODY_R = 15.0
CHILD_R = 8.0
FLASH_RADII = np.arange(7.0, 27.0, 2.5)


def ease_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def fade(t: float, a: float, b: float) -> float:
    """0 before `a`, 1 after `b`, smooth in between."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return ease_in_out((t - a) / (b - a))


class Renderer:
    def __init__(self, history: list[Generation], params: Params, sched: Schedule):
        self.h = history
        self.p = params
        self.sched = sched
        self.bg, self.bg_plain = self._make_background()

        self.body = {r: S.disc(r) for r in np.arange(2.0, 21.0, 1.0)}
        self.glow = S.glow(42.0, 2.6)
        self.glow_small = S.glow(22.0, 2.2)
        self.hilite = S.disc(5.0)
        self.eye_w = S.disc(4.4)
        self.eye_p = S.disc(2.2)
        self.food_dot = S.disc(3.4)
        self.food_glow = S.glow(13.0, 2.2)
        self.flash_rings = [S.ring(r, 2.2) for r in FLASH_RADII]
        self.ring_repro = S.ring(21.0, 3.0)

        self.gen1_hist = history[0].hist.astype(np.float32)
        self.hist_state = history[0].hist.astype(np.float32)
        self.hist_scale = max(6.0, float(history[0].hist.max()))
        self.mean_state = history[0].mean
        self.pop_state = float(len(history[0].speeds))
        self._last_frame = -1
        self.captions = self.build_captions(sched.fps)

    # ------------------------------------------------------------------ bg
    def _make_background(self) -> tuple[np.ndarray, np.ndarray]:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((x - W / 2) / (W * 0.95), (y - (FIELD_Y + FIELD_H / 2)) / (H * 0.62))
        t = np.clip(1.0 - d, 0.0, 1.0)[..., None] ** 1.7
        deep = np.array(C.BG_DEEP, dtype=np.float32)
        glow = np.array(C.BG_GLOW, dtype=np.float32)
        bg = deep + (glow - deep) * t
        plain = bg.copy()

        # field plate + border
        inner = np.zeros((H, W, 1), dtype=np.float32)
        inner[FIELD_Y:FIELD_Y + FIELD_H, FIELD_X:FIELD_X + FIELD_W] = 1.0
        bg += inner * np.array([3.0, 4.0, 9.0], dtype=np.float32)
        edge = np.array(C.FIELD_EDGE, dtype=np.float32) * 0.55
        for off in (0, 1):
            bg[FIELD_Y + off, FIELD_X:FIELD_X + FIELD_W] = edge
            bg[FIELD_Y + FIELD_H - 1 - off, FIELD_X:FIELD_X + FIELD_W] = edge
            bg[FIELD_Y:FIELD_Y + FIELD_H, FIELD_X + off] = edge
            bg[FIELD_Y:FIELD_Y + FIELD_H, FIELD_X + FIELD_W - 1 - off] = edge

        # histogram baseline
        bg[HIST_BASE:HIST_BASE + 2, HIST_X0:HIST_X1] = np.array([58, 68, 96], dtype=np.float32)
        return bg, plain

    # -------------------------------------------------------------- helpers
    def to_px(self, pts: np.ndarray) -> np.ndarray:
        out = np.empty_like(pts)
        out[..., 0] = FIELD_X + FIELD_PAD + pts[..., 0] * (FIELD_W - 2 * FIELD_PAD)
        out[..., 1] = FIELD_Y + FIELD_PAD + pts[..., 1] * (FIELD_H - 2 * FIELD_PAD)
        return out

    def body_for(self, r: float) -> np.ndarray:
        key = float(np.clip(round(r), 2.0, 20.0))
        return self.body[key]

    def creature(self, cv, x, y, hx, hy, col, alpha=1.0, r=BODY_R, eyes=True, glow=1.0):
        if alpha <= 0.01:
            return
        S.blit(cv, self.glow if r > 10 else self.glow_small, x, y, col * 0.42,
               strength=0.50 * alpha * glow, additive=True)
        S.blit(cv, self.body_for(r), x, y, col, strength=alpha)
        S.blit(cv, self.hilite, x - r * 0.32, y - r * 0.38, (255, 255, 255), strength=0.20 * alpha)
        if eyes and r > 9:
            ex, ey = hx * r * 0.40, hy * r * 0.40
            px, py = -hy * r * 0.34, hx * r * 0.34
            for sgn in (-1.0, 1.0):
                bx, by = x + ex + px * sgn, y + ey + py * sgn
                S.blit(cv, self.eye_w, bx, by, (252, 253, 255), strength=alpha)
                S.blit(cv, self.eye_p, bx + hx * 1.7, by + hy * 1.7, (18, 20, 32), strength=alpha)

    # ---------------------------------------------------------------- field
    def draw_field(self, cv, g: Generation, step_f: float, verdict: float, world: float):
        n = len(g.speeds)
        track = g.pos
        last = track.shape[0] - 1
        s0 = int(np.clip(np.floor(step_f), 0, last))
        s1 = min(s0 + 1, last)
        frac = float(np.clip(step_f - s0, 0.0, 1.0))
        pos = track[s0] * (1 - frac) + track[s1] * frac
        px = self.to_px(pos)

        head = track[s1] - track[s0] if s1 > s0 else track[min(1, last)] - track[0]
        hn = np.linalg.norm(head, axis=1, keepdims=True)
        head = np.where(hn > 1e-6, head / np.maximum(hn, 1e-6), np.array([1.0, 0.0]))

        cols = C.speed_color(g.speeds)

        # --- food --------------------------------------------------------
        eaten = g.food_eaten_step
        alive = (eaten < 0) | (eaten > step_f)
        fx = self.to_px(g.food)
        for i in np.flatnonzero(alive):
            S.blit(cv, self.food_glow, fx[i, 0], fx[i, 1], np.array(C.FOOD) * 0.24,
                   strength=0.60 * world, additive=True)
            S.blit(cv, self.food_dot, fx[i, 0], fx[i, 1], C.FOOD, strength=world)

        # --- eat flashes --------------------------------------------------
        age = step_f - eaten + verdict * 3.0   # keep decaying once foraging stops
        recent = np.flatnonzero((eaten >= 0) & (eaten <= step_f) & (age < 3))
        for i in recent:
            u = age[i] / 3.0
            ri = int(np.clip(u * (len(self.flash_rings) - 1), 0, len(self.flash_rings) - 1))
            S.blit(cv, self.flash_rings[ri], fx[i, 0], fx[i, 1], C.FOOD,
                   strength=(1.0 - u) ** 1.5 * 1.25 * world, additive=True)

        # --- motion trails (longer for faster creatures) -------------------
        for k in (3, 2, 1):
            ts = int(np.clip(s0 - k, 0, last))
            tp = self.to_px(track[ts])
            for i in range(n):
                a = (0.16 / k) * world * (0.35 + 0.65 * g.speeds[i])
                S.blit(cv, self.body_for(BODY_R * (1.0 - 0.14 * k)), tp[i, 0], tp[i, 1],
                       cols[i] * 0.75, strength=a)

        # --- bodies -------------------------------------------------------
        for i in range(n):
            alpha, r, col = world, BODY_R, cols[i]
            if verdict > 0.0 and not g.survived[i]:
                k = ease_in_out(min(1.0, verdict / 0.55))
                alpha = world * (1.0 - k)
                r = BODY_R * (1.0 - 0.55 * k)
                col = cols[i] * (1 - k) + np.array(C.DEAD, dtype=np.float32) * k
            self.creature(cv, px[i, 0], px[i, 1], head[i, 0], head[i, 1], col, alpha, r)

            if verdict > 0.0 and g.children[i] > 0:
                k = ease_out(max(0.0, (verdict - 0.30) / 0.70))
                if k > 0.01:
                    S.blit(cv, self.ring_repro, px[i, 0], px[i, 1], cols[i],
                           strength=0.85 * (1.0 - k) ** 1.6 * world, additive=True)
                    ang = np.arctan2(head[i, 1], head[i, 0]) + 2.4
                    cxp = px[i, 0] + np.cos(ang) * 26 * k
                    cyp = px[i, 1] + np.sin(ang) * 26 * k
                    self.creature(cv, cxp, cyp, head[i, 0], head[i, 1], cols[i],
                                  alpha=world * k, r=CHILD_R * k, eyes=False, glow=0.7)

    # ------------------------------------------------------------ histogram
    def draw_hist(self, cv, hist: np.ndarray, mean: float, alpha: float = 1.0,
                  ghost: np.ndarray | None = None, scale: float | None = None):
        if alpha <= 0.01:
            return
        span = HIST_X1 - HIST_X0
        bw = span / HIST_BINS
        sc = scale if scale else self.hist_scale

        if ghost is not None:
            grey = np.array([128, 142, 178], dtype=np.float32)
            for i in range(HIST_BINS):
                hh = int(ghost[i] / sc * HIST_MAXH)
                if hh < 2:
                    continue
                x0 = int(HIST_X0 + i * bw) + 2
                x1 = int(HIST_X0 + (i + 1) * bw) - 2
                body = cv[HIST_BASE - hh:HIST_BASE, x0:x1]
                body *= (1 - 0.16 * alpha)
                body += grey * 0.16 * alpha
                cap = cv[HIST_BASE - hh:HIST_BASE - hh + 3, x0:x1]
                cap *= (1 - 0.55 * alpha)
                cap += grey * 0.55 * alpha

        for i in range(HIST_BINS):
            hh = int(hist[i] / sc * HIST_MAXH)
            if hh < 1:
                continue
            x0 = int(HIST_X0 + i * bw) + 2
            x1 = int(HIST_X0 + (i + 1) * bw) - 2
            col = C.speed_color((i + 0.5) / HIST_BINS)
            ramp = np.linspace(1.0, 0.42, hh, dtype=np.float32)[:, None, None]
            block = col[None, None, :] * ramp
            y0 = HIST_BASE - hh
            dst = cv[y0:HIST_BASE, x0:x1]
            dst *= (1 - alpha)
            dst += block * alpha
            cv[y0:y0 + 3, x0:x1] = cv[y0:y0 + 3, x0:x1] * (1 - alpha) + \
                np.minimum(col * 1.45, 255.0) * alpha

        mx = int(HIST_X0 + mean * span)
        cv[HIST_TOP - 16:HIST_BASE + 2, mx - 1:mx + 2] = \
            cv[HIST_TOP - 16:HIST_BASE + 2, mx - 1:mx + 2] * (1 - 0.8 * alpha) + \
            np.array([255, 255, 255], dtype=np.float32) * 0.8 * alpha

    def draw_legend(self, cv, mean: float, alpha: float = 1.0):
        if alpha <= 0.01:
            return
        span = LEG_X1 - LEG_X0
        ramp = C.speed_color(np.linspace(0, 1, span))
        strip = np.repeat(ramp[None, :, :], LEG_H, axis=0)
        dst = cv[LEG_Y0:LEG_Y0 + LEG_H, LEG_X0:LEG_X1]
        dst *= (1 - alpha)
        dst += strip * alpha
        mx = int(LEG_X0 + mean * span)
        for k in range(9):
            w = 9 - k
            cv[LEG_Y0 - 12 + k, max(LEG_X0, mx - w):min(LEG_X1, mx + w)] = \
                np.array([255, 255, 255], dtype=np.float32)

    # ------------------------------------------------------------- captions
    def build_captions(self, fps: int):
        s = self.sched.slots
        n = len(s)

        def at(g, dur=3.0):
            g = min(g, n - 1)
            return s[g].start, s[g].start + int(dur * fps)

        caps = [
            (int(1.5 * fps), int(3.7 * fps), "速いほど 餌に早く着ける"),
            (int(3.9 * fps), int(6.1 * fps), "でも 速いほど 体力を使う"),
            (int(6.3 * fps), int(8.6 * fps), "餌を集めた個体だけが 子を残す"),
            (*at(3, 2.6), "speedは遺伝する ときどき突然変異"),
            (*at(7, 2.6), "遅い個体から 消えていく"),
            (*at(12, 3.0), "集団の色が 動き出した"),
            (*at(26, 3.0), 'もう "最速" は増えない'),
            (*at(38, 3.0), "ちょうどいい速さに 寄っていく"),
        ]
        seen, out = set(), []
        for a, b, t in caps:
            if a in seen:
                continue
            seen.add(a)
            out.append((a, b, t))
        return out

    def caption_at(self, f: int):
        for a, b, t in self.captions:
            if a <= f < b:
                fps = self.sched.fps
                al = min(fade(f, a, a + 0.3 * fps), 1.0 - fade(f, b - 0.3 * fps, b))
                return t, al
        return "", 0.0

    # ----------------------------------------------------------------- HUD
    def draw_hud(self, ov: Overlay, gen_no: int, pop: float, mean: float,
                 pop_scale: float, alpha: float = 1.0):
        ov.text((HUD_L, HUD_Y), f"第{gen_no}世代", int(56 * pop_scale),
                C.INK, alpha, anchor="lm", shadow=0.5)
        ov.text((HUD_R, HUD_Y - 19), f"個体数 {int(round(pop))}", 34, C.INK_DIM, alpha, anchor="rm")
        col = tuple(int(v) for v in C.speed_color(mean))
        ov.text((HUD_R, HUD_Y + 21), f"平均speed {mean:.2f}", 34, col, alpha, anchor="rm")

    def draw_chrome(self, ov: Overlay, f: int, hook_a: float, hist_a: float):
        ov.text((W // 2, HOOK_Y), "全部同じ色になる?", 86, C.INK, hook_a,
                anchor="mm", stroke=5, shadow=0.6)
        cap, ca = self.caption_at(f)
        if ca > 0:
            ov.text((W // 2, SUB_Y), cap, 40, (196, 208, 236), ca, anchor="mm", shadow=0.5)
        ov.text((HIST_X0, HIST_TITLE_Y), "speed の分布", 32, C.INK_DIM, hist_a, anchor="lm")
        ov.text((HIST_X1, HIST_TITLE_Y), "── 第1世代", 26, (150, 165, 200), hist_a * 0.9,
                anchor="rm")
        ov.text((LEG_X0 - 16, LEG_Y0 + LEG_H / 2), "遅い", 28, (120, 165, 255), hist_a, anchor="rm")
        ov.text((LEG_X1 + 16, LEG_Y0 + LEG_H / 2), "速い", 28, (255, 110, 110), hist_a, anchor="lm")

    # --------------------------------------------------------------- outro
    def grid_positions(self, n: int, top: float, cols: int = 12, dx: float = 80.0,
                       dy: float = 62.0):
        rows = int(np.ceil(n / cols))
        pts = []
        for i in range(n):
            r, c = divmod(i, cols)
            in_row = min(cols, n - r * cols)
            x0 = W / 2 - (in_row - 1) * dx / 2
            pts.append((x0 + c * dx, top + r * dy))
        return pts, rows

    def draw_outro(self, cv, ov: Overlay, f: int):
        fps = self.sched.fps
        span = (self.sched.total - self.sched.gens_end) / fps
        k = span / 10.0           # beats below are written for a 10s outro
        t = (f - self.sched.gens_end) / fps / k
        g1, gz = self.h[0], self.h[-1]

        flash = max(0.0, 1.0 - t / 0.22)
        if flash > 0:
            cv += np.float32(210.0 * flash ** 2)

        ov.text((W // 2, 140), f"第1世代  →  第{len(self.h)}世代", 62, C.INK,
                fade(t, 0.10, 0.6), anchor="mm", stroke=4, shadow=0.5)

        for (gen, label, top, t0) in (
            (g1, "第1世代", 330.0, 0.40),
            (gz, f"第{len(self.h)}世代", 740.0, 1.10),
        ):
            a = fade(t, t0, t0 + 0.45)
            ov.text((W // 2, top - 62), f"{label}　平均 {gen.mean:.2f}", 44,
                    C.INK, a, anchor="mm", shadow=0.5)
            order = np.argsort(gen.speeds)
            pts, _ = self.grid_positions(len(order), top)
            cols_ = C.speed_color(gen.speeds)
            for k, i in enumerate(order):
                ka = fade(t, t0 + 0.12 + k * 0.012, t0 + 0.45 + k * 0.012)
                if ka <= 0.01:
                    continue
                self.creature(cv, pts[k][0], pts[k][1], 1.0, 0.0, cols_[i],
                              alpha=ka, r=21.0 * (0.6 + 0.4 * ka))

        # big converged number
        na = fade(t, 2.2, 2.8)
        if na > 0:
            u = ease_out((t - 2.3) / 1.4)
            val = g1.mean + (gz.mean - g1.mean) * u
            col = tuple(int(v) for v in C.speed_color(val))
            ov.text((W // 2, 1185), f"{val:.2f}", 168, col, na, anchor="mm", stroke=5)
            ov.text((W // 2, 1300), "ちょうどいい速さ", 50, C.INK, fade(t, 3.8, 4.4),
                    anchor="mm", shadow=0.5)

        ov.text((W // 2, 1430), '"最速" が勝つわけじゃない', 54, (255, 214, 120),
                fade(t, 5.0, 5.7), anchor="mm", stroke=4, shadow=0.5)
        ov.text((W // 2, 1520), "速すぎると 体力が足りない", 44, (200, 212, 240),
                fade(t, 6.2, 6.8), anchor="mm", shadow=0.5)
        ov.text((W // 2, 1610), "集団は自分で ちょうどよさを見つけた", 40, C.INK_DIM,
                fade(t, 7.2, 7.8), anchor="mm")

        # legend with both means marked
        la = fade(t, 0.8, 1.4)
        if la > 0:
            span = LEG_X1 - LEG_X0
            ramp = C.speed_color(np.linspace(0, 1, span))
            dst = cv[LEG_Y0:LEG_Y0 + LEG_H, LEG_X0:LEG_X1]
            dst *= (1 - la)
            dst += np.repeat(ramp[None, :, :], LEG_H, axis=0) * la
            for m, up in ((g1.mean, True), (gz.mean, False)):
                mx = int(LEG_X0 + m * span)
                for k in range(9):
                    w = 9 - k
                    yy = LEG_Y0 - 12 + k if up else LEG_Y0 + LEG_H + 11 - k
                    cv[yy, max(LEG_X0, mx - w):min(LEG_X1, mx + w)] = \
                        np.array([255, 255, 255], dtype=np.float32) * la
            ov.text((LEG_X0 - 16, LEG_Y0 + LEG_H / 2), "遅い", 28, (120, 165, 255), la, anchor="rm")
            ov.text((LEG_X1 + 16, LEG_Y0 + LEG_H / 2), "速い", 28, (255, 110, 110), la, anchor="lm")

    # --------------------------------------------------------------- frame
    def seek(self, f: int):
        """Prime the smoothed HUD/histogram state so a single frame can be
        rendered out of order (preview stills)."""
        if f >= self.sched.gens_end:
            g = self.h[-1]
        else:
            g = self.h[self.sched.slot_at(f).gen]
        self.hist_state = g.hist.astype(np.float32)
        self.hist_scale = max(6.0, float(g.hist.max()) * 1.06)
        self.mean_state = g.mean
        self.pop_state = float(len(g.speeds))
        self._last_frame = f - 1

    def render_frame(self, f: int) -> np.ndarray:
        if f != self._last_frame + 1:
            self.seek(f)
        self._last_frame = f
        fps = self.sched.fps
        cv = (self.bg if f < self.sched.gens_end else self.bg_plain).copy()
        ov = Overlay()

        if f < self.sched.gens_end:
            slot = self.sched.slot_at(f)
            g = self.h[slot.gen]
            local = f - slot.start
            world = 1.0

            shown = slot.steps
            if local < slot.forage:
                step_f = (local / max(1, slot.forage)) * shown
                verdict = 0.0
            else:
                step_f = float(shown)
                verdict = (local - slot.forage) / max(1, slot.verdict)

            self.draw_field(cv, g, step_f, verdict, world)

            nxt = self.h[min(slot.gen + 1, len(self.h) - 1)]
            mix = ease_in_out(verdict) if verdict > 0 else 0.0
            tgt_h = g.hist * (1 - mix) + nxt.hist * mix
            tgt_m = g.mean * (1 - mix) + nxt.mean * mix
            tgt_p = len(g.speeds) * (1 - mix) + len(nxt.speeds) * mix

            a = 0.20
            self.hist_state += (tgt_h - self.hist_state) * a
            self.mean_state += (tgt_m - self.mean_state) * a
            self.pop_state += (tgt_p - self.pop_state) * a
            self.hist_scale += (max(6.0, float(tgt_h.max()) * 1.06) - self.hist_scale) * 0.08

            ha = 1.0
            self.draw_hist(cv, self.hist_state, self.mean_state, ha,
                           ghost=self.gen1_hist if slot.gen > 0 else None)
            self.draw_legend(cv, self.mean_state, ha)

            pop_scale = 1.0 + 0.34 * (1.0 - ease_out(local / (0.30 * fps))) if local < 0.30 * fps else 1.0
            if slot.gen > 0 and local < 9:
                cv += np.float32(90.0 * (1.0 - local / 9.0) ** 2)

            self.draw_hud(ov, slot.gen + 1, self.pop_state, self.mean_state, pop_scale, world)
            if verdict > 0.0:
                va = min(fade(verdict, 0.05, 0.28), 1.0 - fade(verdict, 0.82, 1.0))
                died = int((~g.survived).sum())
                born = int(g.children.sum())
                ov.text((W / 2 - 96, FIELD_Y + 44), f"×{died} 死亡", 38,
                        (255, 120, 120), va, anchor="rm", shadow=0.9)
                ov.text((W / 2 + 96, FIELD_Y + 44), f"+{born} 誕生", 38,
                        (140, 240, 160), va, anchor="lm", shadow=0.9)
            self.draw_chrome(ov, f, 1.0, ha)
        else:
            self.draw_outro(cv, ov, f)

        img = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        img.alpha_composite(ov.img)
        return np.asarray(img.convert("RGB"))
