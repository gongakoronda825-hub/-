"""リング脱出レースの物理演算 (pymunk)

画面の中央に 3 重のリング。どのリングにも 1 か所だけ隙間があり、それぞれ違う向き・速さで回る。
真ん中から跳ね回るボールが、3 枚のリングを全部抜けて外に出たら「脱出」。
simulate(seed) で、30fps ごとのボールの位置・角度、ぶつかった音、リングを抜けた瞬間、脱出の時刻を返す。
"""
import math
import random

import pymunk

FPS = 30
SUB = 8
CX, CY = 540, 1000          # リングの中心 (画面の座標)
BALL_R = 34
RINGS = [230, 345, 460]     # リングの半径 (内側から)
RING_W = 9                  # リングの太さ (半分)
GAP = 150                   # 隙間の弧の長さ (px)。ボールの直径 68 の 2 倍ちょっと
MAX_SPEED = 1500

BALL, RING = 1, 2


def layer_of(x, y):
    """いま何枚のリングの外側にいるか (0〜3)"""
    d = math.hypot(x - CX, y - CY)
    return sum(1 for R in RINGS if d > R + RING_W + BALL_R * 0.3)


def simulate(seed, n_balls=6, max_time=60.0, after=10.0):
    rng = random.Random(seed)
    space = pymunk.Space()
    space.gravity = (0, 900)

    rings = []
    for k, R in enumerate(RINGS):
        b = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        b.position = (CX, CY)
        b.angle = rng.uniform(0, 2 * math.pi)
        b.angular_velocity = (1 if k % 2 == 0 else -1) * rng.choice([1, -1]) * rng.uniform(0.7, 1.3)
        space.add(b)
        gap = GAP / R
        n = 72
        for j in range(n):
            a0 = gap + (2 * math.pi - gap) * j / n
            a1 = gap + (2 * math.pi - gap) * (j + 1) / n
            s = pymunk.Segment(b, (R * math.cos(a0), R * math.sin(a0)), (R * math.cos(a1), R * math.sin(a1)), RING_W)
            s.elasticity, s.friction, s.collision_type = 0.97, 0.4, RING
            s.ring_index = k
            space.add(s)
        rings.append(b)

    def limit(body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        if body.velocity.length > MAX_SPEED:
            body.velocity = body.velocity.normalized() * MAX_SPEED

    balls = []
    for i in range(n_balls):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
        a = 2 * math.pi * i / n_balls + rng.uniform(-0.2, 0.2)
        b.position = (CX + 90 * math.cos(a), CY + 90 * math.sin(a))
        b.velocity = (rng.uniform(-500, 500), rng.uniform(-700, -200))
        b.velocity_func = limit
        c = pymunk.Circle(b, BALL_R)
        c.elasticity, c.friction, c.collision_type = 1.0, 0.3, BALL
        c.ball_index = i
        space.add(b, c)
        balls.append(b)

    hits, t_now = [], [0.0]

    def post_solve(arbiter, space_, data):
        imp = arbiter.total_impulse.length
        if imp > 150:
            for s in arbiter.shapes:
                if getattr(s, "ball_index", None) is not None:
                    hits.append((t_now[0], s.ball_index, imp))
                    break

    for a, b in ((BALL, RING), (BALL, BALL)):
        space.on_collision(a, b, post_solve=post_solve)

    frames, escape, passes = [], {}, []
    best = [0] * n_balls                      # これまでに抜けたリングの枚数 (最高記録)
    dt = 1.0 / (FPS * SUB)
    for f in range(int(max_time * FPS)):
        t = f / FPS
        for _ in range(SUB):
            t_now[0] += dt
            space.step(dt)
            for i, b in enumerate(balls):
                if i in escape:
                    continue
                L = layer_of(*b.position)
                if L > best[i]:
                    best[i] = L
                    passes.append((t_now[0], i, L))
                if L == len(RINGS) and math.hypot(b.position.x - CX, b.position.y - CY) > RINGS[-1] + RING_W + BALL_R + 4:
                    escape[i] = t_now[0]
        for i, b in enumerate(balls):
            if i not in escape and b.velocity.length < 60:       # 止まりかけたら少し弾ませる
                b.apply_impulse_at_local_point((rng.uniform(-200, 200), -400))
        frames.append(dict(t=t, balls=[(b.position.x, b.position.y, b.angle) for b in balls],
                           rings=[r.angle for r in rings],
                           layers=[layer_of(*b.position) if i not in escape else len(RINGS) + 1
                                   for i, b in enumerate(balls)]))
        if len(escape) >= 3 and t > sorted(escape.values())[2] + 2.0:
            break
        if escape and t > min(escape.values()) + after:
            break
    return dict(frames=frames, escape=escape, hits=hits, passes=passes)
