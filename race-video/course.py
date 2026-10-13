"""マーブルレースのコースと物理演算 (pymunk)

座標は画面と同じ向き (x: 右, y: 下)。コースの幅は動画と同じ 1080px、縦に長い。
simulate(seed) で、30fps ごとのボールの位置・角度と、ぶつかった音のイベントを返す。
"""
import math
import random

import pymunk

W = 1080
FPS = 30
SUB = 8                    # 1 フレームあたりの物理演算の刻み
R = 50                     # ボールの半径
GATE_OPEN = 3.4            # スタートの仕切りが開く秒 (3・2・1 のあと)
FINISH_Y = 5650            # ゴールライン

BALL, WALL, MOVER = 1, 2, 3


def build(space, rng):
    """静的なコースを作り、描画用の線分リストと回転する羽根のリストを返す"""
    segs, movers = [], []
    static = space.static_body

    def wall(a, b, r=10, bounce=0.35):
        s = pymunk.Segment(static, a, b, r)
        s.elasticity, s.friction, s.collision_type = bounce, 0.25, WALL
        space.add(s)
        segs.append((a, b, r, "wall"))

    def peg(x, y, r=14, kind="peg", bounce=0.6):
        c = pymunk.Circle(static, r, (x, y))
        c.elasticity, c.friction, c.collision_type = bounce, 0.3, WALL
        space.add(c)
        segs.append(((x, y), None, r, kind))

    # 左右の壁
    wall((0, -400), (0, FINISH_Y + 900), 14)
    wall((W, -400), (W, FINISH_Y + 900), 14)
    # スタートのじょうご
    wall((0, 120), (380, 330), 10)
    wall((W, 120), (700, 330), 10)

    # A: ジグザグの坂 (傾きを少しずつ変える)
    y = 520
    for i in range(4):
        tilt = 240 + rng.randint(-30, 30)
        if i % 2 == 0:
            wall((0, y), (800, y + tilt))
        else:
            wall((W, y), (280, y + tilt))
        y += 330
    # B: ピンだらけのエリア
    y0 = 2050
    for row in range(8):                    # 間隔はボールの直径より十分広く、壁からも離す
        off = 0 if row % 2 == 0 else 85
        for col in range(6):
            x = 160 + off + col * 170 + rng.randint(-10, 10)
            if 140 < x < W - 140:
                peg(x, y0 + row * 120)
    # C: 回転する羽根 3 本 (速さ・向きはばらばら)
    y = 3050
    for i, cx in enumerate((300, 780, 540)):
        b = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        b.position = (cx, y + i * 260)
        b.angular_velocity = rng.choice([-1, 1]) * rng.uniform(1.4, 2.4)
        arm = pymunk.Segment(b, (-190, 0), (190, 0), 12)
        arm.elasticity, arm.friction, arm.collision_type = 0.5, 0.5, MOVER
        space.add(b, arm)
        movers.append((b, 190, 12))
    wall((0, 3820), (380, 3960))
    wall((W, 3820), (700, 3960))
    # D: バンパー (よく跳ねる大きい丸)
    for (x, yy) in ((260, 4200), (540, 4380), (820, 4200), (400, 4620), (680, 4620)):
        peg(x + rng.randint(-20, 20), yy, r=48, kind="bumper", bounce=1.05)
    # E: 最後の坂とゴールへのじょうご
    wall((0, 4850), (720, 5060))
    wall((W, 5180), (360, 5390))
    wall((0, 5450), (420, 5560))
    wall((W, 5450), (660, 5560))
    # ゴール後に受け止める床
    wall((0, FINISH_Y + 700), (W, FINISH_Y + 700), 14)
    return segs, movers


def simulate(seed, n_balls=6, max_time=60.0):
    rng = random.Random(seed)
    space = pymunk.Space()
    space.gravity = (0, 1300)
    segs, movers = build(space, rng)

    # スタートの仕切り
    gate = pymunk.Segment(space.static_body, (300, 360), (780, 360), 10)
    gate.elasticity = 0.2
    space.add(gate)

    balls = []
    order = list(range(n_balls))
    rng.shuffle(order)                       # 並ぶ位置はランダム
    for k, idx in enumerate(order):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R))
        b.position = (330 + (k % 3) * 210 + rng.uniform(-6, 6), 200 - (k // 3) * 110)
        c = pymunk.Circle(b, R)
        c.elasticity, c.friction, c.collision_type = 0.45, 0.6, BALL
        c.ball_index = idx
        space.add(b, c)
        balls.append((idx, b))
    balls.sort()

    hits = []                                # (秒, ボール番号, 強さ)
    t_now = [0.0]

    def post_solve(arbiter, space_, data):
        imp = arbiter.total_impulse.length
        if imp > 120:
            for s in arbiter.shapes:
                if getattr(s, "ball_index", None) is not None:
                    hits.append((t_now[0], s.ball_index, imp))
                    break

    for a, b in ((BALL, WALL), (BALL, BALL), (BALL, MOVER)):
        space.on_collision(a, b, post_solve=post_solve)

    frames, finish = [], {}
    dt = 1.0 / (FPS * SUB)
    gate_removed = False
    n = int(max_time * FPS)
    for f in range(n):
        t = f / FPS
        if not gate_removed and t >= GATE_OPEN:
            space.remove(gate)
            gate_removed = True
        for _ in range(SUB):
            t_now[0] += dt
            space.step(dt)
        for idx, b in balls:
            if idx not in finish and b.position.y > FINISH_Y:
                finish[idx] = t + 1.0 / FPS
            # 万一引っかかって止まったら、少しだけ押す
            if b.velocity.length < 3 and b.position.y < FINISH_Y and t > GATE_OPEN + 1:
                b.apply_impulse_at_local_point((rng.uniform(-40, 40), -60))
        frames.append(dict(t=t, balls=[(b.position.x, b.position.y, b.angle) for _, b in balls],
                           movers=[(m.position.x, m.position.y, m.angle) for m, _, _ in movers]))
        if len(finish) == n_balls and t > max(finish.values()) + 2.0:
            break
    return dict(frames=frames, finish=finish, hits=hits, segs=segs,
                movers=[(L, r) for _, L, r in movers])


def leader_changes(res):
    """先頭が何回入れ替わったか (盛り上がりの目安)"""
    last, changes = None, 0
    for fr in res["frames"]:
        if fr["t"] < GATE_OPEN + 1:
            continue
        ys = [y for _, y, _ in fr["balls"]]
        lead = max(range(len(ys)), key=lambda i: ys[i])
        if last is not None and lead != last:
            changes += 1
        last = lead
    return changes
