/*
 * 植物と岩。人類がいないので、建物の代わりにこれが「街の中身」になる。
 *
 * すべて起動時に手続き的に描いて小さなキャンバスに焼く。
 * 焼いたあとは drawImage を並べるだけなので、毎フレームの負荷はほぼゼロ。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});
  const P = FT.pixel;
  const R = FT.rng;

  // パレット（0=透明, 1=輪郭, 2..=暗→明）
  const PAL_TREE = ['', '#16241a', '#23412a', '#2e5532', '#3c6a39', '#4e8144', '#669a52', '#85b465'];
  const PAL_CYCAD = ['', '#132419', '#1b3326', '#26492f', '#33603a', '#437a45', '#569554', '#6fae66'];
  const PAL_FERN = ['', '#17281a', '#1e3520', '#2b4d28', '#3a6830', '#4d853a', '#63a247', '#84bd5c'];
  const PAL_ROCK = ['', '#1d1e1c', '#3c3d3a', '#4f4f4a', '#63625b', '#79786f', '#8f8d82', '#a6a397'];
  const PAL_TRUNK = ['', '#180f0b', '#241a14', '#38271b', '#4b3625', '#5f4730', '#75593c'];
  const PAL_REED = ['', '#1b2a17', '#2c4522', '#3c5c2b', '#4e7636', '#639044', '#7fa85a'];

  const tones = (pal, from, to) => {
    const t = [];
    for (let i = from; i <= to; i++) t.push(i);
    return t;
  };

  function bake(b, pal, outlineIdx, ax, ay, shadow) {
    P.outline(b, outlineIdx);
    return { img: P.toCanvas(b, pal), ax, ay, shadow: shadow || 0 };
  }

  /** シダの葉。中心線に沿って小葉を生やす。 */
  function frond(b, x0, y0, cx, cy, x1, y1, pal, opts) {
    const steps = opts.steps || 26;
    const len = opts.len || 3.2;
    const tone = opts.tones;
    for (let s = 0; s <= steps; s++) {
      const t = s / steps;
      const mt = 1 - t;
      const px = mt * mt * x0 + 2 * mt * t * cx + t * t * x1;
      const py = mt * mt * y0 + 2 * mt * t * cy + t * t * y1;
      const dx = 2 * mt * (cx - x0) + 2 * t * (x1 - cx);
      const dy = 2 * mt * (cy - y0) + 2 * t * (y1 - cy);
      const dl = Math.hypot(dx, dy) || 1;
      const nx = -dy / dl, ny = dx / dl;
      const half = len * Math.pow(Math.sin(Math.PI * Math.min(1, t * 1.05 + 0.08)), 0.7);
      for (let o = -half; o <= half; o += 0.5) {
        // 先端に向かって小葉を間引く＝ギザギザ感
        if (Math.abs(o) > half * 0.55 && ((s + Math.round(o * 2)) & 1) === 0) continue;
        const x = Math.round(px + nx * o);
        const y = Math.round(py + ny * o);
        const k = Math.abs(o) / (half || 1);
        const shade = o < 0 ? 1 - k * 0.55 : 0.62 - k * 0.5; // 左上が明るい
        const idx = tone[R.clamp(Math.floor(shade * tone.length), 0, tone.length - 1)];
        P.set(b, x, y, idx);
      }
      P.set(b, Math.round(px), Math.round(py), tone[Math.max(0, Math.floor(tone.length * 0.35))]);
    }
  }

  function makeTree(rnd, kind) {
    const tall = kind === 'tall';
    const w = tall ? 32 : 30;
    const h = tall ? 58 : 44;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    const trunkH = tall ? 30 : 17;
    // 幹（上に行くほど細く、少し曲げる）
    const bend = (rnd() - 0.5) * 3;
    P.limb(b, [
      [cx, base, tall ? 2.8 : 2.4],
      [cx + bend * 0.5, base - trunkH * 0.55, tall ? 2.2 : 1.9],
      [cx + bend, base - trunkH, tall ? 1.7 : 1.5],
    ], tones(PAL_TRUNK, 2, 6));
    P.limb(b, [[cx - 3.5, base, 1.1], [cx, base - 2, 2.2], [cx + 3.5, base, 1.1]], tones(PAL_TRUNK, 2, 5));

    // 樹冠の塊を先に決める（縦に長い卵形・円錐形）
    const canopyH = tall ? 30 : 20;
    const topY = base - trunkH - canopyH * 0.55;
    const lobes = [];
    const layers = tall ? 7 : 5;
    for (let i = 0; i < layers; i++) {
      const t = i / (layers - 1);                      // 0 = 下, 1 = 上
      const y = base - trunkH + canopyH * 0.45 - canopyH * t;
      const profile = tall
        ? 1 - Math.pow(t, 1.25) * 0.88                  // 円錐
        : Math.sin(Math.PI * (0.22 + t * 0.66)) * 1.05; // 卵形
      const r = (tall ? 8.6 : 10.2) * profile;
      if (r < 1.6) continue;
      const n = r > 6 ? 3 : 2;
      for (let j = 0; j < n; j++) {
        const ang = (j / n) * Math.PI * 2 + rnd() * 2;
        lobes.push({
          x: cx + bend * t + Math.cos(ang) * r * (0.25 + rnd() * 0.42),
          y: y + Math.sin(ang) * r * 0.22,
          r: r * (0.58 + rnd() * 0.28),
        });
      }
      lobes.push({ x: cx + bend * t + (rnd() - 0.5) * 2, y: y - 0.5, r: r * 0.72 });
    }
    // 1) 暗い影の層 → 2) 左上にずらして明るい層。右下に暗い縁が残る。
    const dark = [2, 2, 3];
    for (const l of lobes) P.blob(b, l.x + 0.8, l.y + 1.0, l.r, dark);
    for (const l of lobes) P.blob(b, l.x, l.y, l.r * 0.96, tones(PAL_TREE, 3, 7));
    // 葉の粒立ち
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const v = P.get(b, x, y);
        if (v < 2) continue;
        const n = R.hash2(x, y, 909);
        if (n > 0.88) P.set(b, x, y, Math.max(2, v - 1));
        else if (n < 0.05) P.set(b, x, y, Math.min(7, v + 1));
      }
    }
    return bake(b, PAL_TREE, 1, cx, base + 1, tall ? 9 : 8);
  }

  function makeCycad(rnd) {
    const w = 30, h = 30;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    P.limb(b, [[cx, base, 3.6], [cx, base - 6, 3.2]], tones(PAL_TRUNK, 2, 6));
    const n = 6;
    const top = base - 7;
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1);
      const ang = Math.PI * (0.10 + t * 0.80) + (rnd() - 0.5) * 0.1;
      const rr = 10 + rnd() * 3;
      const ex = cx - Math.cos(ang) * rr;
      const ey = top - Math.sin(ang) * rr * 0.62 + 4;
      frond(b, cx, top, cx - Math.cos(ang) * rr * 0.6, top - Math.sin(ang) * rr * 0.85, ex, ey, PAL_CYCAD, {
        tones: tones(PAL_CYCAD, 2, 7), len: 2.0, steps: 18,
      });
    }
    return bake(b, PAL_CYCAD, 1, cx, base + 1, 7);
  }

  function makeTreeFern(rnd) {
    const w = 34, h = 44;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    const top = base - 26;
    P.limb(b, [[cx, base, 2.6], [cx + 1, base - 14, 2.1], [cx, top, 1.8]], tones(PAL_TRUNK, 2, 5));
    // 幹の鱗
    for (let y = top; y < base - 2; y += 3) {
      P.set(b, cx - 1, Math.round(y), 2);
      P.set(b, cx + 1, Math.round(y + 1.5), 2);
    }
    const n = 6;
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1);
      const ang = Math.PI * (0.06 + t * 0.88) + (rnd() - 0.5) * 0.12;
      const rr = 13 + rnd() * 3;
      const ex = cx - Math.cos(ang) * rr;
      const ey = top - Math.sin(ang) * rr * 0.42 + 8; // 先が垂れる
      frond(b, cx, top, cx - Math.cos(ang) * rr * 0.5, top - Math.sin(ang) * rr * 0.8, ex, ey, PAL_FERN, {
        tones: tones(PAL_FERN, 2, 7), len: 2.4, steps: 22,
      });
    }
    return bake(b, PAL_FERN, 1, cx, base + 1, 8);
  }

  function makeGiantFern(rnd) {
    const w = 30, h = 26;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    const n = 5 + Math.round(rnd() * 2);
    for (let i = 0; i < n; i++) {
      const t = n > 1 ? i / (n - 1) : 0.5;
      const ang = Math.PI * (0.10 + t * 0.80) + (rnd() - 0.5) * 0.14;
      const rr = 10 + rnd() * 4;
      const ex = cx - Math.cos(ang) * rr;
      const ey = base - 3 - Math.sin(ang) * rr * 0.72;
      frond(b, cx, base - 1, cx - Math.cos(ang) * rr * 0.4, base - 2 - Math.sin(ang) * rr * 0.9,
        ex, ey, PAL_FERN, { tones: tones(PAL_FERN, 2, 7), len: 2.2, steps: 18 });
    }
    return bake(b, PAL_FERN, 1, cx, base + 1, 7);
  }

  function makeBush(rnd) {
    const w = 18, h = 14;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    for (let i = 0; i < 4; i++) {
      P.blob(b, cx + (rnd() - 0.5) * 8, base - 3 - rnd() * 4, 3.2 + rnd() * 1.8, tones(PAL_TREE, 2, 7));
    }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const v = P.get(b, x, y);
      if (v > 1 && R.hash2(x, y, 77) > 0.88) P.set(b, x, y, Math.max(2, v - 1));
    }
    return bake(b, PAL_TREE, 1, cx, base + 1, 5);
  }

  function makeRock(rnd, big) {
    const w = big ? 24 : 14, h = big ? 18 : 11;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    const n = big ? 3 : 2;
    for (let i = 0; i < n; i++) {
      const rx = cx + (rnd() - 0.5) * (big ? 9 : 5);
      const ry = base - 2 - rnd() * (big ? 5 : 3);
      P.blob(b, rx, ry, (big ? 5.5 : 3.6) + rnd() * 2, tones(PAL_ROCK, 2, 7));
    }
    // 底を平らに削る
    for (let x = 0; x < w; x++) for (let y = base + 1; y < h; y++) P.set(b, x, y, 0);
    // ひび
    for (let i = 0; i < (big ? 3 : 2); i++) {
      let x = Math.round(cx + (rnd() - 0.5) * w * 0.5);
      let y = Math.round(base - 3 - rnd() * 4);
      for (let s = 0; s < (big ? 6 : 4); s++) {
        if (P.get(b, x, y) > 1) P.set(b, x, y, 2);
        x += rnd() > 0.5 ? 1 : 0;
        y += 1;
      }
    }
    return bake(b, PAL_ROCK, 1, cx, base + 1, big ? 7 : 4);
  }

  function makeReed(rnd) {
    const w = 16, h = 16;
    const b = P.buf(w, h);
    const cx = w >> 1, base = h - 2;
    const n = 5 + Math.round(rnd() * 3);
    for (let i = 0; i < n; i++) {
      const x0 = cx + (rnd() - 0.5) * 8;
      const lean = (rnd() - 0.5) * 6;
      const len = 5 + rnd() * 7;
      P.limb(b, [[x0, base, 0.6], [x0 + lean * 0.5, base - len * 0.6, 0.5], [x0 + lean, base - len, 0.4]],
        tones(PAL_REED, 3, 6));
    }
    return bake(b, PAL_REED, 1, cx, base + 1, 3);
  }

  function makeLog(rnd) {
    const w = 26, h = 12;
    const b = P.buf(w, h);
    const base = h - 3;
    P.limb(b, [[3, base, 2.6], [w - 4, base - 1, 2.4]], tones(PAL_TRUNK, 2, 6));
    P.blob(b, w - 4, base - 1, 2.4, tones(PAL_TRUNK, 2, 5));
    for (let i = 0; i < 6; i++) {
      const x = 5 + Math.round(rnd() * (w - 10));
      P.set(b, x, base - 2, 2);
    }
    // 苔
    for (let x = 3; x < w - 4; x++) {
      if (R.hash2(x, 3, 12) > 0.6) P.set(b, x, base - 3, 3);
    }
    return bake(b, PAL_TRUNK, 1, w >> 1, base + 2, 6);
  }

  function buildCatalog(seed) {
    const rnd = R.mulberry32(seed + 4242);
    const cat = { tree: [], cycad: [], treefern: [], fern: [], bush: [], rock: [], reed: [], log: [] };
    for (let i = 0; i < 4; i++) cat.tree.push(makeTree(rnd, i % 2 === 0 ? 'tall' : 'round'));
    for (let i = 0; i < 3; i++) cat.cycad.push(makeCycad(rnd));
    for (let i = 0; i < 3; i++) cat.treefern.push(makeTreeFern(rnd));
    for (let i = 0; i < 4; i++) cat.fern.push(makeGiantFern(rnd));
    for (let i = 0; i < 3; i++) cat.bush.push(makeBush(rnd));
    for (let i = 0; i < 3; i++) cat.rock.push(makeRock(rnd, i === 0));
    for (let i = 0; i < 3; i++) cat.reed.push(makeReed(rnd));
    cat.log.push(makeLog(rnd));
    return cat;
  }

  /** 地形の上に植物を撒く。森は固まって、水辺には葦、高地には岩。 */
  function scatter(world, cat, seed) {
    const rnd = R.mulberry32(seed + 99);
    const items = [];
    const pick = (arr) => arr[Math.floor(rnd() * arr.length) % arr.length];

    world.forEachTileInRect(-40, -60, world.width + 40, world.height + 60, (tx, ty) => {
      if (world.isWater(tx, ty)) return;
      const h = world.heightOf(tx, ty);
      const forestV = world.forestAt(tx, ty);
      const lushV = world.lushAt(tx, ty);
      const rocky = world.rockyAt(tx, ty);
      const nearWater =
        world.isWater(tx + 1, ty) || world.isWater(tx - 1, ty) ||
        world.isWater(tx, ty + 1) || world.isWater(tx, ty - 1);

      let kind = null;
      const r = rnd();
      if (nearWater) {
        if (r < 0.13) kind = 'reed';
        else if (r < 0.18) kind = 'fern';
        else if (r < 0.21) kind = 'rock';
      } else if (rocky) {
        if (r < 0.08) kind = 'rock';
        else if (r < 0.10) kind = 'bush';
      } else if (forestV > 0.62) {
        const dense = (forestV - 0.62) * 2.8;
        if (r < 0.24 * dense) kind = 'tree';
        else if (r < 0.24 * dense + 0.05) kind = 'treefern';
        else if (r < 0.24 * dense + 0.09) kind = 'fern';
        else if (r < 0.24 * dense + 0.11) kind = 'bush';
      } else {
        if (r < 0.012) kind = lushV > 0.55 ? 'cycad' : 'bush';
        else if (r < 0.024) kind = 'fern';
        else if (r < 0.030) kind = 'tree';
        else if (r < 0.036) kind = 'rock';
        else if (r < 0.038) kind = 'log';
      }
      if (!kind) return;

      const sprite = pick(cat[kind]);
      const p = world.project(tx, ty, h);
      // タイル内でばらけさせる（菱形の中に収める）
      const a = (rnd() - 0.5) * 0.8, b2 = (rnd() - 0.5) * 0.8;
      const jx = Math.round((a - b2) * (world.TW / 2));
      const jy = Math.round((a + b2) * (world.TH / 2));
      items.push({
        x: p.x + jx,
        y: p.y + jy,
        depth: tx + ty + a + b2,
        sprite,
      });
    });

    items.sort((p, q) => p.depth - q.depth);
    return items;
  }

  /** 雲の影。地面の上をゆっくり流れると、世界が「生きている」ように見える。 */
  function buildCloudShadows(seed, count) {
    const rnd = R.mulberry32(seed + 555);
    const out = [];
    for (let i = 0; i < (count || 3); i++) {
      const w = 130 + Math.round(rnd() * 90);
      const h = 54 + Math.round(rnd() * 34);
      const cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      const ctx = cv.getContext('2d');
      const img = ctx.createImageData(w, h);
      const data = new Uint32Array(img.data.buffer);
      const lobes = [];
      const n = 4 + Math.floor(rnd() * 3);
      for (let j = 0; j < n; j++) {
        lobes.push({
          x: w * (0.22 + rnd() * 0.56),
          y: h * (0.28 + rnd() * 0.44),
          rx: w * (0.16 + rnd() * 0.20),
          ry: h * (0.22 + rnd() * 0.26),
        });
      }
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          let cover = 0;
          for (const l of lobes) {
            const nx = (x - l.x) / l.rx, ny = (y - l.y) / l.ry;
            cover = Math.max(cover, 1 - (nx * nx + ny * ny));
          }
          if (cover <= 0) continue;
          let a = Math.min(1, cover * 2.6) * 0.15;
          if (cover < 0.28 && ((x + y) & 1) === 0) a *= 0.3;
          if (a <= 0.004) continue;
          data[y * w + x] = (Math.round(a * 255) << 24) | (46 << 16) | (30 << 8) | 14;
        }
      }
      ctx.putImageData(img, 0, 0);
      out.push(cv);
    }
    return out;
  }

  FT.props = { buildCatalog, scatter, buildCloudShadows };
})(window);
