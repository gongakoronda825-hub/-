#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok向け縦型シミュレーション動画ジェネレータ。

回転するリングの中でボールが跳ね、バウンドのたびに大きく・速くなる。
リングには隙間が1つあり、そこから脱出できるか / 育ちすぎて閉じ込められるかを見守る。

物理: 円の内壁に対するベクトル反射の自前実装（gap判定を角度で直接扱うため）。
描画: Pillow。2倍解像度で描いてから縮小（アンチエイリアス）。
音  : numpyで生成したブリップ＋決着SEをWAVに書き出し、ffmpegでミックス。
"""

import argparse
import colorsys
import math
import os
import random
import subprocess
import sys
import time
import wave
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920          # 出力解像度（縦型）
S = 2                      # スーパーサンプリング倍率
FONT_JP = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"

TAU = math.pi * 2


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


def ang_diff(a, b):
    """a-b を [-pi, pi) に正規化"""
    d = (a - b + math.pi) % TAU - math.pi
    return d


def hsv(h, s=0.72, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


# --------------------------------------------------------------------------
# パラメータ
# --------------------------------------------------------------------------
@dataclass
class Params:
    seed: int = 0
    cx: float = W * 0.5
    cy: float = 1022.0
    R_in: float = 452.0        # 内壁半径（ボール中心の可動域は R_in - r）
    ring_w: float = 27.0
    gap_half: float = math.radians(10.0)
    gap0: float = 0.0
    omega: float = 0.3         # リング回転 [rad/s]
    r0: float = 18.0
    grow_r: float = 1.015      # バウンドごとの半径倍率
    v0: float = 700.0
    grow_v: float = 1.008      # バウンドごとの速度倍率
    v_max: float = 1700.0
    gravity: float = 480.0
    jitter: float = math.radians(1.2)
    hue0: float = 0.0
    hue_step: float = 0.037

    @property
    def R_out(self):
        return self.R_in + self.ring_w

    @property
    def R_fill(self):
        return self.R_in * 0.82

    @property
    def r_fit(self):
        """この半径を超えると隙間を物理的に通れない"""
        return self.R_in * math.sin(self.gap_half)


def sample_params(seed):
    rng = random.Random(seed)
    p = Params(seed=seed)
    p.gap_half = math.radians(rng.uniform(8.6, 11.4))
    p.gap0 = rng.uniform(0, TAU)
    p.omega = rng.choice((1, -1)) * rng.uniform(0.20, 0.42)
    p.r0 = rng.uniform(16.0, 20.0)
    p.grow_r = rng.uniform(1.0090, 1.0125)
    p.v0 = rng.uniform(650.0, 785.0)
    p.grow_v = rng.uniform(1.0058, 1.0102)
    p.gravity = rng.uniform(380.0, 620.0)
    p.hue0 = rng.random()
    p.hue_step = rng.choice((1, -1)) * rng.uniform(0.028, 0.048)
    return p


# --------------------------------------------------------------------------
# シミュレーション（円内壁のベクトル反射）
# --------------------------------------------------------------------------
class Sim:
    SUB = 4  # 1フレームあたりの物理サブステップ

    def __init__(self, p: Params):
        self.p = p
        self.rng = random.Random(p.seed ^ 0x5EED5EED)
        a = self.rng.uniform(0, TAU)
        d0 = p.R_in * self.rng.uniform(0.10, 0.40)
        self.x = p.cx + d0 * math.cos(a)
        self.y = p.cy + d0 * math.sin(a)
        th = self.rng.uniform(0, TAU)
        self.vx = p.v0 * math.cos(th)
        self.vy = p.v0 * math.sin(th)
        self.r = p.r0
        self.vt = p.v0                 # 目標速度（バウンドごとに更新）
        self.gap = p.gap0
        self.bounces = 0
        self.t = 0.0
        self.phase = "run"             # run / escape / trapped
        self.phase_t = 0.0
        self.hue = p.hue0
        self.hue_tgt = p.hue0
        self.passing = False
        self.outcome_t = None
        self.final_bounces = 0
        self.r_trap = p.r0
        self.v_trap = p.v0

    # ---------------- 物理 ----------------
    def _wall(self, dt, ev):
        p = self.p
        if self.phase == "escape":
            return
        dx = self.x - p.cx
        dy = self.y - p.cy
        d = math.hypot(dx, dy) or 1e-9
        lim = p.R_in - self.r

        if self.phase == "run" and self.passing:
            if d < lim:                       # 戻ってきた（惜しい！）
                self.passing = False
            elif d > p.R_out + self.r * 0.2:  # 完全に外へ
                self._on_escape(ev)
            return

        if d <= lim:
            return

        nx, ny = dx / d, dy / d
        ang = math.atan2(dy, dx)

        # 隙間を通れるか（ボールの角サイズを考慮）
        if self.phase == "run":
            half_ball = math.asin(clamp(self.r / p.R_in, 0.0, 1.0))
            if abs(ang_diff(ang, self.gap)) + half_ball <= p.gap_half:
                self.passing = True
                return

        # 反射
        vn = self.vx * nx + self.vy * ny
        if vn > 0:
            self.vx -= 2 * vn * nx
            self.vy -= 2 * vn * ny
        self.x = p.cx + nx * lim
        self.y = p.cy + ny * lim

        # 接線方向の微小ジッタ（積分可能性を壊してリング全体を舐めさせる）
        j = self.rng.uniform(-p.jitter, p.jitter)
        c, s = math.cos(j), math.sin(j)
        self.vx, self.vy = self.vx * c - self.vy * s, self.vx * s + self.vy * c

        self.bounces += 1
        if self.phase == "run":
            self.r = min(self.r * p.grow_r, p.R_fill)
            self.vt = min(self.vt * p.grow_v, p.v_max)
            self.hue_tgt += p.hue_step

        sp = math.hypot(self.vx, self.vy) or 1e-9
        k = self.vt / sp
        self.vx *= k
        self.vy *= k

        if self.phase == "run" or self.phase_t < 1.3:
            ev.append(("bounce", p.cx + nx * p.R_in, p.cy + ny * p.R_in,
                       self.vt, self.r, self.hue_tgt, ang))

        if self.phase == "run" and self.r >= p.r_fit * 0.995:
            self._on_trap(ev)

    def _on_escape(self, ev):
        self.phase = "escape"
        self.phase_t = 0.0
        self.outcome_t = self.t
        self.final_bounces = self.bounces
        ev.append(("escape", self.x, self.y, self.vt, self.r, self.hue_tgt, 0.0))

    def _on_trap(self, ev):
        self.phase = "trapped"
        self.phase_t = 0.0
        self.outcome_t = self.t
        self.final_bounces = self.bounces
        self.r_trap = self.r
        self.v_trap = self.vt
        ev.append(("trap", self.x, self.y, self.vt, self.r, self.hue_tgt, 0.0))

    def _phys(self, dt, ev):
        p = self.p
        self.gap += p.omega * dt
        self.vy += p.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._wall(dt, ev)
        self.hue += (self.hue_tgt - self.hue) * min(1.0, dt * 14.0)

    # ---------------- 決着後の時間スケール（スローモー） ----------------
    def timescale(self):
        u = self.phase_t
        if self.phase == "escape":
            if u < 0.12:
                return lerp(1.0, 0.28, u / 0.12)
            if u < 1.5:
                return 0.28
            if u < 2.3:
                return lerp(0.28, 1.0, (u - 1.5) / 0.8)
        elif self.phase == "trapped":
            if u < 0.10:
                return lerp(1.0, 0.45, u / 0.10)
            if u < 1.1:
                return 0.45
            if u < 1.9:
                return lerp(0.45, 1.0, (u - 1.1) / 0.8)
        return 1.0

    def advance_frame(self, dt):
        ev = []
        if self.phase == "trapped":
            # 決着後はボールが膨らんでリングを埋めていく
            u = min(1.0, self.phase_t / 3.4)
            self.r = lerp(self.r_trap, self.p.R_fill, ease_out(u))
            self.vt = max(28.0, self.v_trap * (1.0 - u) ** 1.6)
            self.hue_tgt += 0.12 * dt
        sub = dt * self.timescale() / self.SUB
        for _ in range(self.SUB):
            self._phys(sub, ev)
        self.t += dt
        if self.phase != "run":
            self.phase_t += dt
        return ev


# --------------------------------------------------------------------------
# シード探索: 決着が「動画の終盤」に来る展開だけを採用する
# --------------------------------------------------------------------------
def headless(p, duration, fps, stop_on_outcome=True):
    sim = Sim(p)
    dt = 1.0 / fps
    frames = int(round(duration * fps))
    out = []
    for i in range(frames):
        ev = sim.advance_frame(dt)
        if ev:
            out.append((i, ev))
        if stop_on_outcome and sim.phase != "run":
            break
    return sim, out


def pick_run(base_seed, duration, fps, lo, hi, tries=8000, budget=40.0):
    """決着時刻が [lo, hi] に入るシードを探す。

    結末は毎回変わってほしいので、まず「脱出」/「閉じ込め」のどちらを狙うかを
    コイントスで決め、その結末になるシードを優先して採用する。
    見つからなければ窓内の別結末 -> 一番近いもの、の順にフォールバック。
    """
    t0 = time.time()
    rng = random.Random(base_seed)
    want = "escape" if rng.random() < 0.5 else "trapped"
    other = None
    best = None
    tried = 0
    for _ in range(tries):
        tried += 1
        p = sample_params(rng.getrandbits(40))
        sim, _ = headless(p, min(duration, hi + 1.0), fps)
        if sim.phase == "run":
            continue
        t_out = sim.outcome_t
        if lo <= t_out <= hi:
            if sim.phase == want:
                return p, sim.phase, t_out, sim.final_bounces, tried
            if other is None:
                other = (p, sim.phase, t_out, sim.final_bounces)
        score = min(abs(t_out - lo), abs(t_out - hi))
        if best is None or score < best[0]:
            best = (score, p, sim.phase, t_out, sim.final_bounces)
        if time.time() - t0 > budget:
            break
    if other is not None:
        return other + (tried,)
    if best is None:
        p = sample_params(rng.getrandbits(40))
        return p, "run", duration, 0, tried
    return best[1], best[2], best[3], best[4], tried


# --------------------------------------------------------------------------
# 見た目の状態（トレイル / 波紋 / 粒子 / シェイク / フラッシュ）
# --------------------------------------------------------------------------
class Visuals:
    TRAIL = 34

    def __init__(self, p):
        self.p = p
        self.trail = []
        self.ripples = []      # [x, y, age, life, r0, r1, hue]
        self.parts = []        # [x, y, vx, vy, life, life0, r, hue]
        self.shake = 0.0
        self.shake_ph = 0.0
        self.flash = 0.0
        self.ring_pulse = 0.0
        self.rng = random.Random(p.seed ^ 0xA11CE)
        self.last_rip = -9.0

    def update(self, sim, ev, dt):
        self.trail.append((sim.x, sim.y, sim.r, sim.hue))
        if len(self.trail) > self.TRAIL:
            del self.trail[0]

        for e in ev:
            kind, x, y, sp, r, hue, ang = e
            if kind == "bounce":
                if sim.t - self.last_rip > 0.045:
                    self.last_rip = sim.t
                    rv = min(r, 88.0)
                    self.ripples.append([x, y, 0.0, 0.45, rv * 0.55, rv * 2.1, hue])
                self.ring_pulse = 1.0
                # 大きく育ったボールが当たった時だけ軽くシェイク
                thr = self.p.r_fit * 0.45
                if r > thr:
                    amp = clamp((r - thr) / (self.p.R_in * 0.5), 0.0, 1.0)
                    self.shake = max(self.shake, 4.0 + 16.0 * amp)
                    self.shake_ph = self.rng.uniform(0, TAU)
            elif kind == "escape":
                self.flash = 0.62
                self.shake = max(self.shake, 10.0)
                for _ in range(46):
                    a = self.rng.uniform(0, TAU)
                    s = self.rng.uniform(120, 620)
                    life = self.rng.uniform(0.7, 2.0)
                    self.parts.append([x, y, math.cos(a) * s, math.sin(a) * s,
                                       life, life, self.rng.uniform(3, 9),
                                       hue + self.rng.uniform(-0.08, 0.08)])
            elif kind == "trap":
                self.flash = 0.34
                self.shake = max(self.shake, 20.0)

        for rp in self.ripples:
            rp[2] += dt
        self.ripples = [r for r in self.ripples if r[2] < r[3]]

        g = self.p.gravity * 0.45
        for q in self.parts:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += g * dt
            q[4] -= dt
        self.parts = [q for q in self.parts if q[4] > 0]

        self.shake *= math.exp(-dt * 8.5)
        self.shake_ph += dt * 46.0
        self.flash = max(0.0, self.flash - dt * 2.1)
        self.ring_pulse = max(0.0, self.ring_pulse - dt * 4.0)

    def shake_offset(self):
        if self.shake < 0.25:
            return 0.0, 0.0
        return (math.sin(self.shake_ph * 1.7) * self.shake,
                math.cos(self.shake_ph * 2.3) * self.shake * 0.8)


# --------------------------------------------------------------------------
# 描画
# --------------------------------------------------------------------------
class Renderer:
    RING_COL = (198, 226, 255)
    GW, GH = W // 4, H // 4

    def __init__(self, p: Params, duration):
        self.p = p
        self.duration = duration
        self.bg = self._background()
        self.fonts = {}
        self.f_hook = self.font(96)
        self.f_sub = self.font(34)
        self.f_cnt = self.font(46)

    def font(self, size):
        size = int(size)
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(FONT_JP, size)
        return self.fonts[size]

    def _background(self):
        """淡いグラデーション＋ビネットの暗背景（2倍解像度）"""
        h2, w2 = H * S, W * S
        yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32)
        yy /= h2
        xx /= w2
        top = np.array([16, 20, 34], np.float32)
        bot = np.array([6, 7, 14], np.float32)
        img = top[None, None, :] * (1 - yy)[..., None] + bot[None, None, :] * yy[..., None]
        # リング中心あたりをほんのり持ち上げる
        cx, cy = self.p.cx / W, self.p.cy / H
        d = np.sqrt(((xx - cx) * (W / H)) ** 2 + (yy - cy) ** 2)
        halo = np.clip(1.0 - d / 0.42, 0, 1) ** 2
        img += halo[..., None] * np.array([20, 28, 56], np.float32)
        # ビネット
        vig = np.clip(1.0 - (d / 0.78) ** 2.2, 0.35, 1.0)
        img *= vig[..., None]
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")

    # ---------------- リング ----------------
    def _ring(self, dr, sim, vis, ox, oy):
        p = self.p
        cx = p.cx * S + ox
        cy = p.cy * S + oy
        mid = (p.R_in + p.ring_w * 0.5) * S
        wdt = p.ring_w * S
        a1 = math.degrees(sim.gap + p.gap_half)
        a2 = math.degrees(sim.gap + TAU - p.gap_half)

        glow = mix((26, 44, 86), (70, 110, 180), vis.ring_pulse * 0.6)
        dr.arc((cx - mid, cy - mid, cx + mid, cy + mid), a1, a2,
               fill=mix(glow, (10, 14, 26), 0.55), width=int(wdt * 3.4))
        dr.arc((cx - mid, cy - mid, cx + mid, cy + mid), a1, a2,
               fill=glow, width=int(wdt * 2.0))
        col = mix(self.RING_COL, (255, 255, 255), vis.ring_pulse * 0.5)
        dr.arc((cx - mid, cy - mid, cx + mid, cy + mid), a1, a2,
               fill=col, width=int(wdt))

        # 隙間の端をまるくして、出口を目立たせる
        for sgn in (1, -1):
            a = sim.gap + sgn * p.gap_half
            x = cx + math.cos(a) * mid
            y = cy + math.sin(a) * mid
            rr = wdt * 0.5
            dr.ellipse((x - rr * 1.55, y - rr * 1.55, x + rr * 1.55, y + rr * 1.55),
                       fill=mix(glow, (150, 200, 255), 0.45))
            dr.ellipse((x - rr * 0.95, y - rr * 0.95, x + rr * 0.95, y + rr * 0.95),
                       fill=(240, 249, 255))

    # ---------------- 半透明レイヤー ----------------
    # 奥（リングの下）: トレイル   手前（リングの上）: 波紋・粒子・ボール
    def _prims_back(self, sim, vis, ox, oy):
        """トレイル。外側の淡い層 -> 内側の明るい芯、の2パスで柔らかい縁を作る"""
        pts = vis.trail
        n = len(pts)
        if n < 2:
            return []
        samples = []
        for i in range(n - 1):
            x0, y0, r0_, h0 = pts[i]
            x1, y1, r1_, h1 = pts[i + 1]
            seg = math.hypot(x1 - x0, y1 - y0)
            steps = max(1, min(7, int(seg / max(2.0, r0_ * 0.30)) + 1))
            for k in range(steps):
                f = k / steps
                u = (i + f) / (n - 1)
                samples.append(((x0 + (x1 - x0) * f) * S + ox,
                                (y0 + (y1 - y0) * f) * S + oy,
                                min(r0_, 88.0) * S, u, h0 + (h1 - h0) * f))
        prims = []
        for scale, alpha, sat in ((1.85, 0.30, 0.45), (1.18, 0.55, 0.55), (0.72, 1.0, 0.66)):
            for x, y, rb, u, hue in samples:
                a = int(132 * alpha * u ** 2.0)
                if a < 5:
                    continue
                prims.append(("c", x, y, rb * (0.09 + 0.56 * u) * scale,
                              hsv(hue, sat, 1.0) + (a,)))
        return prims

    def _prims_front(self, sim, vis, ox, oy):
        prims = []

        def sx(v):
            return v * S + ox

        def sy(v):
            return v * S + oy

        # 波紋（着弾点から広がる衝撃リング）
        for rx, ry, age, life, r0, r1, hue in vis.ripples:
            u = age / life
            rad = lerp(r0, r1, ease_out(u)) * S
            a = int(125 * (1 - u) ** 2.0)
            if a > 4:
                prims.append(("o", sx(rx), sy(ry), rad, max(2, int(2.6 * S * (1 - u) + 1.2)),
                              hsv(hue, 0.45, 1.0) + (a,)))

        # 粒子
        for qx, qy, _, _, life, life0, qr, hue in vis.parts:
            u = life / life0
            a = int(235 * u ** 1.3)
            prims.append(("c", sx(qx), sy(qy), qr * S * (0.4 + 0.6 * u),
                          hsv(hue, 0.5, 1.0) + (a,)))

        # ボール本体
        big = clamp((sim.r - 90.0) / 260.0, 0.0, 1.0)
        bc = hsv(sim.hue, 0.70 + 0.10 * big, 1.0 - 0.22 * big)
        rr = sim.r * S
        if sim.phase == "trapped":
            rr *= 1.0 + 0.012 * math.sin(sim.phase_t * 4.2)
        prims.append(("c", sx(sim.x), sy(sim.y), rr * 1.10, mix(bc, (0, 0, 0), 0.55) + (110,)))
        prims.append(("c", sx(sim.x), sy(sim.y), rr, bc + (255,)))
        prims.append(("c", sx(sim.x) - rr * 0.26, sy(sim.y) - rr * 0.30, rr * 0.46,
                      mix(bc, (255, 255, 255), 0.50 - 0.28 * big) + (255,)))
        prims.append(("o", sx(sim.x), sy(sim.y), rr * 0.97, max(2, int(rr * 0.07)),
                      mix(bc, (255, 255, 255), 0.42) + (255,)))
        return prims

    def _blit(self, img, prims):
        if not prims:
            return
        x0 = y0 = 1e9
        x1 = y1 = -1e9
        for pr in prims:
            if pr[0] == "l":
                _, ax, ay, bx, by, wdt, _ = pr
                m = wdt
                x0 = min(x0, ax - m, bx - m); x1 = max(x1, ax + m, bx + m)
                y0 = min(y0, ay - m, by - m); y1 = max(y1, ay + m, by + m)
            else:
                _, ax, ay, rad = pr[0], pr[1], pr[2], pr[3]
                m = rad + (pr[4] if pr[0] == "o" else 0) + 2
                x0 = min(x0, ax - m); x1 = max(x1, ax + m)
                y0 = min(y0, ay - m); y1 = max(y1, ay + m)
        x0 = int(max(0, x0)); y0 = int(max(0, y0))
        x1 = int(min(W * S, x1 + 1)); y1 = int(min(H * S, y1 + 1))
        if x1 <= x0 or y1 <= y0:
            return
        ov = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for pr in prims:
            if pr[0] == "c":
                _, ax, ay, rad, col = pr
                ax -= x0; ay -= y0
                d.ellipse((ax - rad, ay - rad, ax + rad, ay + rad), fill=col)
            elif pr[0] == "o":
                _, ax, ay, rad, wdt, col = pr
                ax -= x0; ay -= y0
                d.ellipse((ax - rad, ay - rad, ax + rad, ay + rad), outline=col, width=int(wdt))
            else:
                _, ax, ay, bx, by, wdt, col = pr
                d.line((ax - x0, ay - y0, bx - x0, by - y0), fill=col, width=int(wdt))
        img.paste(ov, (x0, y0), ov)

    # ---------------- 発光レイヤー（1/4解像度でぼかして加算） ----------------
    def _glow(self, small, sim, vis, ox, oy):
        p = self.p
        k = 1.0 / 4.0
        g = Image.new("RGB", (self.GW, self.GH), (0, 0, 0))
        d = ImageDraw.Draw(g)
        cx = (p.cx + ox / S) * k
        cy = (p.cy + oy / S) * k
        mid = (p.R_in + p.ring_w * 0.5) * k
        a1 = math.degrees(sim.gap + p.gap_half)
        a2 = math.degrees(sim.gap + TAU - p.gap_half)
        d.arc((cx - mid, cy - mid, cx + mid, cy + mid), a1, a2,
              fill=(30, 48, 80), width=max(1, int(p.ring_w * k)))
        pts = vis.trail
        for i in range(0, len(pts) - 1, 2):
            tx, ty, tr, th = pts[i]
            u = (i + 1) / len(pts)
            rad = min(tr, 88.0) * k * (0.5 + 1.3 * u)
            d.ellipse(((tx + ox / S) * k - rad, (ty + oy / S) * k - rad,
                       (tx + ox / S) * k + rad, (ty + oy / S) * k + rad),
                      fill=mix(hsv(th, 0.55, 1.0), (0, 0, 0), 1.0 - 0.34 * u ** 2))
        bc = hsv(sim.hue, 0.62, 1.0)
        bx = (sim.x + ox / S) * k
        by = (sim.y + oy / S) * k
        rad = sim.r * k
        if sim.r < 110.0:
            d.ellipse((bx - rad * 2.4, by - rad * 2.4, bx + rad * 2.4, by + rad * 2.4),
                      fill=mix(bc, (0, 0, 0), 0.76))
            d.ellipse((bx - rad * 1.15, by - rad * 1.15, bx + rad * 1.15, by + rad * 1.15),
                      fill=mix(bc, (0, 0, 0), 0.42))
        else:
            hal = rad + 58.0 * k
            d.ellipse((bx - hal, by - hal, bx + hal, by + hal), fill=mix(bc, (0, 0, 0), 0.74))
            cut = rad * 0.93
            d.ellipse((bx - cut, by - cut, bx + cut, by + cut), fill=(0, 0, 0))
        for qx, qy, _, _, life, life0, qr, hue in vis.parts:
            u = life / life0
            d.ellipse(((qx + ox / S) * k - qr * k * 3, (qy + oy / S) * k - qr * k * 3,
                       (qx + ox / S) * k + qr * k * 3, (qy + oy / S) * k + qr * k * 3),
                      fill=mix(hsv(hue, 0.5, 1.0), (0, 0, 0), 1 - 0.5 * u))
        g = g.filter(ImageFilter.GaussianBlur(5))
        g = g.resize((W, H), Image.BILINEAR)
        return ImageChops.add(small, g)

    # ---------------- 文字 ----------------
    def _text(self, d, xy, txt, font, fill, anchor="mm", stroke=None, shadow=True):
        x, y = xy
        sw = max(1, font.size // 16) if stroke is None else stroke
        if shadow:
            d.text((x, y + max(2, font.size // 22)), txt, font=font, fill=(0, 0, 0),
                   anchor=anchor, stroke_width=sw + 2, stroke_fill=(0, 0, 0))
        d.text((x, y), txt, font=font, fill=fill, anchor=anchor,
               stroke_width=sw, stroke_fill=fill)

    def _hud(self, small, sim, vis):
        d = ImageDraw.Draw(small)
        t = sim.t
        pulse = 0.5 + 0.5 * math.sin(t * 2.3)
        bob = math.sin(t * 2.0) * 4
        self._text(d, (W * 0.5, 176 + bob), "脱出できる？", self.f_hook,
                   mix((232, 240, 255), (255, 255, 255), pulse))
        self._text(d, (W * 0.5, 268), "リングは回る。ボールは育つ。", self.f_sub,
                   (150, 166, 196), stroke=1)
        n = sim.final_bounces if sim.phase != "run" else sim.bounces
        self._text(d, (W - 62, 372), "バウンド: %d" % n, self.f_cnt,
                   (214, 226, 250), anchor="rm", stroke=1)
        # 隙間を通れる残りサイズのメーター
        frac = clamp(sim.r / self.p.r_fit, 0.0, 1.0)
        bw, bh = 300, 10
        bx, by = W - 62 - bw, 424
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh // 2, fill=(32, 38, 56))
        col = mix((94, 226, 168), (255, 96, 110), frac ** 1.4)
        d.rounded_rectangle((bx, by, bx + max(bh, bw * frac), by + bh), radius=bh // 2, fill=col)

    def _result(self, small, sim):
        if sim.phase == "run" or sim.phase_t < 0.18:
            return
        u = clamp((sim.phase_t - 0.18) / 0.34, 0.0, 1.0)
        pop = 1.0 + 0.22 * (1 - ease_out(u)) - 0.10 * math.sin(min(1, u) * math.pi)
        win = sim.phase == "escape"
        txt = "脱出成功！" if win else "閉じ込められた…"
        sub = "%d回でクリア" % sim.final_bounces if win else "%d回で限界…" % sim.final_bounces
        col = (120, 255, 196) if win else (255, 122, 132)
        size = int(clamp(112 * pop, 40, 150))
        if not win:
            size = int(size * 0.74)
        f = self.font(size)
        fs = self.font(int(size * 0.38))
        cy = self.p.cy
        # 可読性用の暗いパネル
        bb = ImageDraw.Draw(small).textbbox((W * 0.5, cy - 44), txt, font=f, anchor="mm")
        pad = 46
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.7, bb[2] + pad, cy + 104),
                             radius=34, fill=(6, 8, 16, int(188 * clamp(u * 1.6, 0, 1))))
        small.paste(Image.alpha_composite(small.convert("RGBA"), ov).convert("RGB"), (0, 0))
        d = ImageDraw.Draw(small)
        self._text(d, (W * 0.5, cy - 44), txt, f, col)
        self._text(d, (W * 0.5, cy + 62), sub, fs, (210, 220, 240), stroke=1)

    # ---------------- 1フレーム ----------------
    def frame(self, sim, vis):
        ox, oy = vis.shake_offset()
        ox *= S
        oy *= S
        img = self.bg.copy()
        dr = ImageDraw.Draw(img)
        self._blit(img, self._prims_back(sim, vis, ox, oy))   # トレイルはリングの奥
        self._ring(dr, sim, vis, ox, oy)
        self._blit(img, self._prims_front(sim, vis, ox, oy))  # ボールはリングの手前
        small = img.reduce(S)
        small = self._glow(small, sim, vis, ox, oy)
        if vis.flash > 0.004:
            white = Image.new("RGB", (W, H), (255, 255, 255))
            small = Image.blend(small, white, clamp(vis.flash, 0, 0.85))
        self._hud(small, sim, vis)
        self._result(small, sim)
        return small


# --------------------------------------------------------------------------
# 音
# --------------------------------------------------------------------------
PENTA = [0, 2, 4, 7, 9]


def _add(buf, t, sig, sr):
    i = int(t * sr)
    if i < 0:
        return
    n = min(len(sig), len(buf) - i)
    if n > 0:
        buf[i:i + n] += sig[:n]


def _blip(freq, amp, sr, dur=0.30):
    tt = np.arange(int(dur * sr), dtype=np.float32) / sr
    env = np.exp(-tt / 0.085) * (1 - np.exp(-tt / 0.0018))
    w = (np.sin(TAU * freq * tt)
         + 0.30 * np.sin(TAU * 2 * freq * tt) * np.exp(-tt / 0.030)
         + 0.14 * np.sin(TAU * 3 * freq * tt) * np.exp(-tt / 0.014))
    return (amp * env * w).astype(np.float32)


def make_audio(events, duration, path, phase, hold=1.0, sr=44100):
    n = int((duration + 0.6) * sr)
    buf = np.zeros(n, np.float32)
    bi = 0
    for fi, evs in events:
        for kind, x, y, sp, r, hue, ang in evs:
            t = fi / 60.0
            if kind == "bounce":
                if t > duration - hold:   # 最後の静止中は鳴らさない
                    continue
                deg = PENTA[bi % 5] + 12 * ((bi // 5) % 3)
                f = 246.94 * (2 ** (deg / 12.0))
                amp = 0.46 * clamp(0.45 + sp / 2400.0, 0.3, 1.0)
                _add(buf, t, _blip(f, amp, sr), sr)
                bi += 1
            elif kind == "escape":
                for k, semi in enumerate((0, 4, 7, 12, 16)):
                    _add(buf, t + k * 0.075,
                         _blip(392.0 * 2 ** (semi / 12.0), 0.44, sr, 0.9), sr)
                tt = np.arange(int(1.4 * sr), dtype=np.float32) / sr
                sweep = (np.sin(TAU * (600 + 1800 * tt) * tt) * np.exp(-tt / 0.28) * 0.14)
                _add(buf, t, sweep.astype(np.float32), sr)
            elif kind == "trap":
                tt = np.arange(int(2.2 * sr), dtype=np.float32) / sr
                thud = np.sin(TAU * 62 * tt) * np.exp(-tt / 0.40) * 0.40
                down = np.sin(TAU * (380 - 230 * np.clip(tt / 1.4, 0, 1)) * tt) * np.exp(-tt / 0.70) * 0.20
                noise = (np.random.RandomState(7).randn(len(tt)).astype(np.float32)
                         * np.exp(-tt / 0.06) * 0.10)
                _add(buf, t, (thud + down + noise).astype(np.float32), sr)
    # ピーク正規化だと「音数の少ない回」だけ極端に大きくなるので固定ゲイン＋ソフトクリップ
    buf = np.tanh(buf / 0.85) * 0.89
    pcm = (buf * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="output/escape.mp4")
    ap.add_argument("--duration", type=float, default=70.0)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--preview", action="store_true", help="1フレームだけPNGで出す")
    ap.add_argument("--preview-at", type=float, default=14.0)
    ap.add_argument("--preview-out", default="output/preview.png")
    ap.add_argument("--render-seconds", type=float, default=None, help="短縮テスト用")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--hold", type=float, default=1.0, help="最後の静止秒数")
    ap.add_argument("--search-budget", type=float, default=40.0)
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else int.from_bytes(os.urandom(5), "big")
    dur = args.duration
    fps = args.fps
    hold = args.hold
    # 決着は「終盤」に来てほしい（残りがオチの見せ場）
    lo = max(8.0, dur - 14.0)
    hi = dur - hold - 2.2

    print("[seed] base=%d" % seed)
    t0 = time.time()
    p, phase, t_out, nb, tried = pick_run(seed, dur, fps, lo, hi, budget=args.search_budget)
    print("[pick] %d候補 %.1fs -> 決着=%s t=%.1fs bounces=%d seed=%d"
          % (tried, time.time() - t0, phase, t_out, nb, p.seed))
    print("[params] gap=%.1f° omega=%+.2f r0=%.1f grow_r=%.4f v0=%.0f grow_v=%.4f g=%.0f r_fit=%.0f"
          % (math.degrees(p.gap_half) * 2, p.omega, p.r0, p.grow_r, p.v0, p.grow_v,
             p.gravity, p.r_fit))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    rend = Renderer(p, dur)

    if args.preview:
        sim = Sim(p)
        vis = Visuals(p)
        dt = 1.0 / fps
        for _ in range(int(args.preview_at * fps)):
            vis.update(sim, sim.advance_frame(dt), dt)
        os.makedirs(os.path.dirname(os.path.abspath(args.preview_out)) or ".", exist_ok=True)
        rend.frame(sim, vis).save(args.preview_out)
        print("[preview] %s (t=%.1fs, r=%.1f, bounces=%d)"
              % (args.preview_out, sim.t, sim.r, sim.bounces))
        return

    # --- 音用に先にフル尺を回してイベントを収集（物理は決定論的なので再現する） ---
    audio_path = None
    if not args.no_audio:
        _, evs = headless(p, dur, fps, stop_on_outcome=False)
        audio_path = os.path.join(os.path.dirname(os.path.abspath(args.out)), "escape_audio.wav")
        make_audio(evs, dur, audio_path, phase, hold)
        print("[audio] %s" % audio_path)

    total = int(round((args.render_seconds or dur) * fps))
    freeze_at = int(round((dur - hold) * fps))

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(fps), "-i", "-"]
    if audio_path:
        cmd += ["-i", audio_path]
    cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-movflags", "+faststart", args.out]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sim = Sim(p)
    vis = Visuals(p)
    dt = 1.0 / fps
    last = None
    t0 = time.time()
    for i in range(total):
        if i < freeze_at or last is None:
            vis.update(sim, sim.advance_frame(dt), dt)
            last = rend.frame(sim, vis).tobytes()
        proc.stdin.write(last)
        if i % 120 == 0 and i:
            el = time.time() - t0
            print("  %5d/%d  %.1f fps  ETA %.0fs" % (i, total, i / el, el / i * (total - i)),
                  flush=True)
    proc.stdin.close()
    proc.wait()
    print("[done] %s  %.1fs で描画  結末=%s (%d bounces)"
          % (args.out, time.time() - t0, phase, nb))


if __name__ == "__main__":
    main()
