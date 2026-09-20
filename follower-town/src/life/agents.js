/*
 * 恐竜のふるまい。
 *
 * 全員が同じ動きをすると作り物に見えるので、待機時間・移動方向・速度・
 * 歩き始めの位相を個体ごとにばらす。水には入らず、崖は登らない。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});
  const P = FT.pixel;
  const R = FT.rng;

  // 1歩（脚の1周期）で進む画面px。歩幅と速度を合わせて足が滑らないようにする。
  const CYCLE_PX = { sauropod: 8.5, stego: 6.0, raptor: 5.0 };
  // 種ごとの移動速度（タイル/秒）。1タイル ≒ 画面 8.9px。
  const SPEED = {
    sauropod: [0.30, 0.52],
    stego: [0.45, 0.80],
    raptor: [1.5, 2.6],
  };

  function createLife(world, sprites, seed, cfg) {
    const rnd = R.mulberry32(seed + 777);
    const agents = [];
    const flyers = [];
    const shadows = {};
    for (const key of Object.keys(sprites)) {
      const sh = sprites[key].shadow;
      shadows[key] = P.shadowSprite(sh[0], sh[1], 0.34);
    }

    // 歩き回ってよい範囲（ワールドバッファの内側）
    const bounds = { x0: 60, y0: 90, x1: world.width - 60, y1: world.height - 70 };

    function inBounds(tx, ty) {
      const p = world.project(tx, ty);
      return p.x > bounds.x0 && p.x < bounds.x1 && p.y > bounds.y0 && p.y < bounds.y1;
    }

    function walkable(tx, ty, fromH) {
      const rx = Math.round(tx), ry = Math.round(ty);
      if (!world.inGrid(rx, ry)) return false;
      if (world.isWater(rx, ry)) return false;
      if (Math.abs(world.heightOf(rx, ry) - fromH) > 1.01) return false;
      return inBounds(tx, ty);
    }

    function findSpot(near) {
      for (let i = 0; i < 400; i++) {
        const tx = near.tx + (rnd() - 0.5) * near.spread;
        const ty = near.ty + (rnd() - 0.5) * near.spread;
        const rx = Math.round(tx), ry = Math.round(ty);
        if (!world.inGrid(rx, ry) || world.isWater(rx, ry)) continue;
        if (!inBounds(tx, ty)) continue;
        return { tx, ty };
      }
      return { tx: near.tx, ty: near.ty };
    }

    function spawn(kind, spot) {
      const sp = sprites[kind];
      const a = {
        kind,
        sp,
        tx: spot.tx,
        ty: spot.ty,
        face: rnd() > 0.5 ? 1 : -1,
        state: 'idle',
        clip: 'idle',
        frame: Math.floor(rnd() * 8),
        ftime: rnd() * 4,
        fps: 4,
        timer: 0.5 + rnd() * 5,
        vx: 0,
        vy: 0,
        speed: 0,
        drawY: null,
      };
      agents.push(a);
      return a;
    }

    function chooseHeading(a) {
      const h = world.heightOf(Math.round(a.tx), Math.round(a.ty));
      for (let i = 0; i < 24; i++) {
        const ang = rnd() * Math.PI * 2;
        const dx = Math.cos(ang), dy = Math.sin(ang);
        // 画面上での進行方向。横移動を少し優先して、歩いている姿が見えやすいように
        const ttx = dx * 0.7 + dy * 0.7;
        const tty = -dx * 0.7 + dy * 0.7;
        if (walkable(a.tx + ttx * 3, a.ty + tty * 3, h)) {
          const sr = SPEED[a.kind] || [0.5, 1];
          a.speed = R.lerp(sr[0], sr[1], rnd()) * (a.clip === 'run' ? 2.1 : 1);
          a.vx = ttx * a.speed;
          a.vy = tty * a.speed;
          const sdx = (a.vx - a.vy) * world.TW * 0.5;
          if (Math.abs(sdx) > 0.05) a.face = sdx > 0 ? 1 : -1;
          return true;
        }
      }
      return false;
    }

    function nextState(a) {
      const r = rnd();
      const canGraze = a.sp.clips.graze !== undefined;
      const canRun = a.sp.clips.run !== undefined;
      if (a.state === 'walk' || a.state === 'run') {
        a.state = r < 0.45 && canGraze ? 'graze' : 'idle';
      } else if (r < 0.52) {
        a.state = canRun && r < 0.18 ? 'run' : 'walk';
      } else if (r < 0.78 && canGraze) {
        a.state = 'graze';
      } else {
        a.state = a.sp.clips.look && r > 0.93 ? 'look' : 'idle';
      }

      a.vx = a.vy = 0;
      if (a.state === 'walk' || a.state === 'run') {
        a.clip = a.state === 'run' && canRun ? 'run' : 'walk';
        if (!chooseHeading(a)) { a.state = 'idle'; a.clip = 'idle'; }
        a.timer = 3 + rnd() * (a.state === 'run' ? 3 : 9);
      } else if (a.state === 'graze') {
        a.clip = 'graze';
        a.ftime = 0;
        a.fps = a.sp.clips.graze.length / (4.5 + rnd() * 3);
        a.timer = a.sp.clips.graze.length / a.fps;
      } else if (a.state === 'look') {
        a.clip = 'look';
        a.ftime = 0;
        a.fps = a.sp.clips.look.length / 2.6;
        a.timer = a.sp.clips.look.length / a.fps;
      } else {
        a.clip = 'idle';
        a.fps = 2.4 + rnd() * 1.6;
        a.timer = 2 + rnd() * 7;
      }
      if (a.clip === 'walk' || a.clip === 'run') {
        const px = a.speed * world.TW * 0.5 * Math.hypot(1, 0.5); // ≒ タイル/秒 → px/秒
        const cyc = CYCLE_PX[a.kind] || 6;
        a.fps = R.clamp((px / cyc), 0.4, 4.2) * a.sp.clips[a.clip].length;
      }
    }

    function updateAgent(a, dt) {
      a.timer -= dt;
      if (a.timer <= 0) nextState(a);

      if (a.vx || a.vy) {
        const h = world.heightOf(Math.round(a.tx), Math.round(a.ty));
        const nx = a.tx + a.vx * dt, ny = a.ty + a.vy * dt;
        if (walkable(nx + a.vx * 0.9, ny + a.vy * 0.9, h)) {
          a.tx = nx; a.ty = ny;
        } else if (!chooseHeading(a)) {
          a.vx = a.vy = 0;
          a.state = 'idle'; a.clip = 'idle'; a.timer = 1 + rnd() * 3;
        }
      }

      const frames = a.sp.clips[a.clip] || a.sp.clips.idle;
      a.ftime += dt * a.fps;
      a.frame = Math.floor(a.ftime) % frames.length;
    }

    // ── 翼竜 ───────────────────────────────────
    let flyerTimer = 4 + rnd() * 6;
    function spawnFlyer(opts) {
      opts = opts || {};
      const sp = sprites.ptero;
      const dir = opts.dir || (rnd() > 0.5 ? 1 : -1);
      const view = opts.view || { x: 0, y: 0, w: world.width, h: world.height };
      const y = opts.y !== undefined ? opts.y : view.y + view.h * (0.18 + rnd() * 0.45);
      flyers.push({
        sp,
        x: dir > 0 ? view.x - 40 : view.x + view.w + 40,
        y,
        alt: opts.alt !== undefined ? opts.alt : 26 + rnd() * 26,
        vx: dir * (opts.speed || 34 + rnd() * 26),
        vy: (rnd() - 0.5) * 5,
        face: dir,
        ftime: rnd() * 5,
        fps: 7 + rnd() * 3,
        frame: 0,
        life: 0,
      });
    }

    function updateFlyers(dt, view) {
      flyerTimer -= dt;
      if (flyerTimer <= 0) {
        const iv = cfg.PTERO_INTERVAL;
        flyerTimer = iv[0] + rnd() * (iv[1] - iv[0]);
        spawnFlyer({ view, count: 1 });
        if (rnd() > 0.55) {
          const extra = 1 + Math.floor(rnd() * 2);
          for (let i = 0; i < extra; i++) spawnFlyer({ view });
        }
      }
      for (let i = flyers.length - 1; i >= 0; i--) {
        const f = flyers[i];
        f.x += f.vx * dt;
        f.y += f.vy * dt;
        f.life += dt;
        f.ftime += dt * f.fps;
        f.frame = Math.floor(f.ftime) % f.sp.clips.fly.length;
        if (f.x < view.x - 120 || f.x > view.x + view.w + 120 || f.life > 60) flyers.splice(i, 1);
      }
    }

    function update(dt, view) {
      for (const a of agents) updateAgent(a, dt);
      updateFlyers(dt, view);
    }

    /** 描画順に並べるためのエントリを集める。 */
    function collect(out, view) {
      for (const a of agents) {
        const p = world.project(a.tx, a.ty);
        if (p.x < view.x - 60 || p.x > view.x + view.w + 60) continue;
        if (p.y < view.y - 80 || p.y > view.y + view.h + 80) continue;
        a.sx = p.x; a.sy = p.y;
        out.push({ depth: a.tx + a.ty, agent: a });
      }
    }

    function drawAgent(ctx, a, cam) {
      const sp = a.sp;
      const frames = sp.clips[a.clip] || sp.clips.idle;
      const img = frames[a.frame % frames.length];
      // 高さの段差でガタつかないよう、表示yだけ追従させる
      if (a.drawY === null) a.drawY = a.sy;
      a.drawY += (a.sy - a.drawY) * 0.22;
      const x = Math.round(a.sx - cam.x);
      const y = Math.round(a.drawY - cam.y);
      const sh = shadows[a.kind];
      if (sh) ctx.drawImage(sh, x - ((sh.width / 2) | 0), y - ((sh.height / 2) | 0) + 1);
      const ax = sp.anchor[0], ay = sp.anchor[1];
      if (a.face > 0) {
        ctx.drawImage(img, x - ax, y - ay);
      } else {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(-1, 1);
        ctx.drawImage(img, -(sp.w - ax), -ay);
        ctx.restore();
      }
    }

    function drawFlyerShadows(ctx, cam) {
      const sh = shadows.ptero;
      if (!sh) return;
      ctx.globalAlpha = 0.5;
      for (const f of flyers) {
        const x = Math.round(f.x - cam.x), y = Math.round(f.y - cam.y);
        ctx.drawImage(sh, x - ((sh.width / 2) | 0), y - ((sh.height / 2) | 0));
      }
      ctx.globalAlpha = 1;
    }

    function drawFlyers(ctx, cam) {
      for (const f of flyers) {
        const img = f.sp.clips.fly[f.frame % f.sp.clips.fly.length];
        const x = Math.round(f.x - cam.x);
        const y = Math.round(f.y - f.alt - cam.y);
        const ax = f.sp.anchor[0], ay = f.sp.anchor[1];
        if (f.face > 0) {
          ctx.drawImage(img, x - ax, y - ay);
        } else {
          ctx.save();
          ctx.translate(x, y);
          ctx.scale(-1, 1);
          ctx.drawImage(img, -(f.sp.w - ax), -ay);
          ctx.restore();
        }
      }
    }

    /** 群れを撒く。中心付近に、種類ごとに散らして置く。 */
    function populate(center) {
      const herd = cfg.HERD;
      for (const kind of Object.keys(herd)) {
        const n = herd[kind];
        for (let i = 0; i < n; i++) {
          const spread = kind === 'raptor' ? 10 : 26;
          const base = kind === 'raptor'
            ? { tx: center.tx + (rnd() - 0.5) * 14, ty: center.ty + (rnd() - 0.5) * 14, spread }
            : { tx: center.tx, ty: center.ty, spread: 34 };
          const spot = findSpot(base);
          const a = spawn(kind, spot);
          nextState(a);
          a.timer = rnd() * 6;
        }
      }
    }

    return {
      agents, flyers, populate, update, collect,
      drawAgent, drawFlyers, drawFlyerShadows, spawnFlyer,
    };
  }

  FT.life = { createLife };
})(window);
