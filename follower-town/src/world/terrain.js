/*
 * 地形。クォータービュー（斜め上から見下ろす）のタイルを1枚の大きな
 * オフスクリーンキャンバスに焼き込む。毎フレーム描き直すのは動くものだけ。
 *
 * タイルは 16x8 の菱形。高さは1段 5px で、段差の側面（土の壁）も描くので
 * 丘と崖の高低差が出る。色はタイル単位ではなく、隣タイルとの補間＋画素ごとの
 * ディザで決めるので、マス目が見えない自然な草原になる。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});
  const R = FT.rng;

  const TW = 16, TH = 8, LEVEL = 4;
  const HW = TW / 2, HH = TH / 2;
  const WATER_H = 1.6;      // 水面の高さ（陸の最低 2 より少し低い）
  const MIN_LAND = 2, MAX_LAND = 6;

  const ROW_LEFT = [7, 5, 3, 1, 1, 3, 5, 7];
  const ROW_WIDTH = [2, 6, 10, 14, 14, 10, 6, 2];
  const COL_BOTTOM = (() => {
    const t = new Int8Array(TW).fill(-1);
    for (let r = 0; r < TH; r++) {
      for (let x = ROW_LEFT[r]; x < ROW_LEFT[r] + ROW_WIDTH[r]; x++) t[x] = r;
    }
    return t;
  })();

  const pack = (r, g, b) => ((255 << 24) | (b << 16) | (g << 8) | r) >>> 0;
  const ramp = (list) => list.map((c) => pack(c[0], c[1], c[2]));

  // ── パレット（暗→明） ─────────────────────────────
  const GRASS = ramp([
    [47, 78, 45], [58, 92, 50], [70, 108, 56], [84, 124, 62], [99, 140, 70], [116, 156, 80],
  ]);
  const DRY = ramp([
    [86, 96, 52], [102, 111, 58], [119, 127, 66], [137, 142, 76], [154, 156, 88],
  ]);
  const ROCKY = ramp([
    [72, 74, 68], [88, 89, 81], [104, 104, 95], [120, 119, 108], [136, 134, 122],
  ]);
  const SAND = ramp([
    [150, 134, 96], [168, 152, 112], [186, 170, 128], [201, 186, 145],
  ]);
  const WATER = ramp([
    [22, 52, 74], [26, 64, 88], [32, 80, 104], [40, 98, 120], [52, 117, 136], [70, 138, 152],
  ]);
  const FOAM = ramp([[150, 196, 200], [186, 221, 220], [214, 238, 235]]);
  const DIRT = ramp([
    [62, 48, 34], [78, 60, 42], [94, 73, 50], [110, 86, 59], [124, 100, 68],
  ]);
  const DIRT_DARK = ramp([
    [46, 36, 26], [58, 45, 32], [70, 55, 39], [82, 65, 46], [94, 76, 54],
  ]);
  // 1段だけの段差は土ではなく「草の斜面」にする。地形が縞に見えなくなる。
  const SLOPE = ramp([
    [40, 64, 38], [48, 74, 44], [56, 84, 48], [64, 92, 54],
  ]);
  const SLOPE_DARK = ramp([
    [32, 52, 32], [40, 62, 38], [48, 72, 43], [54, 80, 47],
  ]);
  const FLOWERS = ramp([[214, 222, 198], [226, 196, 208], [230, 214, 150], [198, 208, 226]]);

  function pickTone(list, t, jitter) {
    const n = list.length;
    let i = Math.floor(R.clamp(t + jitter, 0, 0.9999) * n);
    return list[R.clamp(i, 0, n - 1)];
  }

  function create(opts) {
    const seed = opts.seed | 0;
    const W = opts.width, H = opts.height;
    const originX = Math.round(W / 2);
    const originY = 30;

    const DMAX = Math.ceil((W / 2 + TW) / HW) + 1;
    const KMAX = Math.ceil((H + 96 + MAX_LAND * LEVEL - originY) / HH);
    const MINT = -DMAX - 4;
    const MAXT = Math.ceil((KMAX + DMAX) / 2) + 4;
    const GN = MAXT - MINT + 1;

    const height = new Float32Array(GN * GN);
    const water = new Uint8Array(GN * GN);
    const depth = new Float32Array(GN * GN);
    const lush = new Float32Array(GN * GN);
    const dry = new Float32Array(GN * GN);
    const rocky = new Uint8Array(GN * GN);
    const forest = new Float32Array(GN * GN);
    const at = (tx, ty) => (ty - MINT) * GN + (tx - MINT);
    const inGrid = (tx, ty) => tx >= MINT && ty >= MINT && tx <= MAXT && ty <= MAXT;

    // ── 川と池の形 ────────────────────────────────
    // k = tx+ty が画面の縦、d = tx-ty が画面の横に対応する。
    // 川は縦方向に蛇行させ、どの画角でも必ず横切るようにする。
    function riverCenter(k) {
      return 13 * Math.sin(k * 0.0208) + 7.5 * Math.sin(k * 0.0096 + 1.7) - 1;
    }
    function riverWidth(k) {
      return 3.0 + 1.1 * Math.sin(k * 0.031 + 0.6);
    }
    const PONDS = [
      { k: 86, d: -19, rk: 15, rd: 8 },
      { k: 172, d: 18, rk: 13, rd: 7 },
    ];

    function waterAmount(k, d) {
      // 戻り値 > 0 なら水。値は深さ 0..1
      const rd = Math.abs(d - riverCenter(k));
      // 岸の線をわざと乱す。これがないと川が定規で引いた線になる。
      const wob = R.noise2(k * 0.11, d * 0.11, seed + 31) * 1.2 - 0.6 +
        (R.noise2(k * 0.42, d * 0.42, seed + 37) - 0.5) * 0.9;
      const rw = riverWidth(k);
      let amount = (rw + wob - rd) / rw;
      for (const p of PONDS) {
        const nk = (k - p.k) / p.rk, nd = (d - p.d) / p.rd;
        const e = 1 - (nk * nk + nd * nd);
        if (e > amount) amount = e;
      }
      return amount;
    }

    for (let ty = MINT; ty <= MAXT; ty++) {
      for (let tx = MINT; tx <= MAXT; tx++) {
        const i = at(tx, ty);
        const k = tx + ty, d = tx - ty;
        const big = R.fbm(tx * 0.0095, ty * 0.0095, seed + 101, 2);
        const mid = R.fbm(tx * 0.027, ty * 0.027, seed + 7, 3);
        let v = Math.pow(R.clamp(big * 0.62 + mid * 0.38, 0, 1), 1.5);
        let h = MIN_LAND + v * (MAX_LAND - MIN_LAND + 0.9);

        const wa = waterAmount(k, d);
        if (wa > 0) {
          water[i] = 1;
          depth[i] = R.clamp(wa, 0, 1);
          height[i] = WATER_H;
        } else {
          // 岸に近いほど低くする（川に向かって土地が下がる）
          const bank = R.smoothstep(-1.6, 0, wa);
          h = R.lerp(h, MIN_LAND + 0.2, bank);
          // 段の境目をわざとギザつかせる。これをしないと等高線が
          // 画面を横切る長い直線になって、畑のうねのように見えてしまう。
          const jitter = (R.noise2(tx * 0.115, ty * 0.115, seed + 301) - 0.5) * 0.75 +
            (R.noise2(tx * 0.33, ty * 0.33, seed + 307) - 0.5) * 0.3;
          height[i] = R.clamp(Math.round(h + jitter), MIN_LAND, MAX_LAND);
        }

        const moisture = R.clamp(1 - Math.abs(d - riverCenter(k)) / 26, 0, 1);
        lush[i] = R.clamp(
          0.22 + R.fbm(tx * 0.048 + 40, ty * 0.048, seed + 5, 3) * 0.52 +
            R.noise2(tx * 0.17, ty * 0.17, seed + 71) * 0.22 + moisture * 0.22 -
            (height[i] - MIN_LAND) * 0.035,
          0, 1
        );
        dry[i] = R.fbm(tx * 0.026, ty * 0.026, seed + 61, 3) + (height[i] - MIN_LAND) * 0.03;
        rocky[i] = height[i] >= 6 && R.fbm(tx * 0.08, ty * 0.08, seed + 77, 2) > 0.52 ? 1 : 0;
        forest[i] = R.fbm(tx * 0.062 + 13, ty * 0.062 + 9, seed + 23, 3);
      }
    }

    const heightOf = (tx, ty) => (inGrid(tx, ty) ? height[at(tx, ty)] : MIN_LAND);
    const isWater = (tx, ty) => (inGrid(tx, ty) ? water[at(tx, ty)] === 1 : false);

    // ── ラスタライズ ───────────────────────────────
    const canvas = document.createElement('canvas');
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext('2d');
    const img = ctx.createImageData(W, H);
    const buf = new Uint32Array(img.data.buffer);
    buf.fill(pack(18, 26, 30));

    const sparkles = [];
    const put = (x, y, c) => {
      if (x < 0 || y < 0 || x >= W || y >= H) return;
      buf[y * W + x] = c;
    };

    for (let k = 0; k <= KMAX; k++) {
      let dStart = -DMAX;
      if ((((dStart + k) % 2) + 2) % 2 !== 0) dStart++;
      for (let dd = dStart; dd <= DMAX; dd += 2) {
        const tx = (k + dd) >> 1, ty = (k - dd) >> 1;
        if (!inGrid(tx, ty)) continue;
        const i = at(tx, ty);
        const h = height[i];
        const bx = originX + dd * HW - HW;
        const by = Math.round(originY + k * HH - h * LEVEL) - HH;
        if (bx >= W || bx + TW < 0 || by >= H) continue;

        const isW = water[i] === 1;
        const hL = heightOf(tx, ty + 1);   // 左下の隣（画面の左下方向）
        const hR = heightOf(tx + 1, ty);   // 右下の隣
        const wallL = Math.min(48, Math.max(0, Math.round((h - hL) * LEVEL)));
        const wallR = Math.min(48, Math.max(0, Math.round((h - hR) * LEVEL)));
        if (by + TH + Math.max(wallL, wallR) < 0) continue;

        // 高い隣接タイルの方向（崖下の接地影用）
        const aoA = heightOf(tx - 1, ty) > h ? 1 : 0;  // 画面の左上側
        const aoB = heightOf(tx, ty - 1) > h ? 1 : 0;  // 画面の右上側

        const nLush = lush[i], nDry = dry[i], nRock = rocky[i];
        const lushR = inGrid(tx + 1, ty) ? lush[at(tx + 1, ty)] : nLush;
        const lushL = inGrid(tx - 1, ty) ? lush[at(tx - 1, ty)] : nLush;
        const lushD = inGrid(tx, ty + 1) ? lush[at(tx, ty + 1)] : nLush;
        const lushU = inGrid(tx, ty - 1) ? lush[at(tx, ty - 1)] : nLush;

        // 岸（水に隣り合う陸）判定
        const wR = isWater(tx + 1, ty), wL = isWater(tx - 1, ty);
        const wD = isWater(tx, ty + 1), wU = isWater(tx, ty - 1);
        const anyShore = !isW && (wR || wL || wD || wU);

        for (let r = 0; r < TH; r++) {
          const y = by + r;
          if (y < 0 || y >= H) continue;
          const left = ROW_LEFT[r], wd = ROW_WIDTH[r];
          for (let c = 0; c < wd; c++) {
            const lx = left + c;
            const x = bx + lx;
            if (x < 0 || x >= W) continue;
            const ddx = lx - 7.5, ddy = r - 3.5;
            const a = ddx / TW + ddy / TH;        // tx 方向 -0.5..0.5
            const b = ddy / TH - ddx / TW;        // ty 方向 -0.5..0.5
            const n = R.hash2(x, y, seed + 3);

            let col;
            if (isW) {
              const dp = depth[i];
              const band = R.noise2(x * 0.09, y * 0.22, seed + 13);
              let t = R.clamp(0.95 - dp * 0.80 + band * 0.24 - 0.12, 0, 0.999);
              col = pickTone(WATER, t, (n - 0.5) * 0.10);
              if (dp < 0.20 && n > 0.66) col = WATER[5];
              if (dp < 0.09 && n > 0.80) col = FOAM[0];
            } else {
              // 隣タイルと補間して、マス目を見せない
              const lv = nLush + (a >= 0 ? (lushR - nLush) * a * 2 : (lushL - nLush) * -a * 2) * 0.5 +
                (b >= 0 ? (lushD - nLush) * b * 2 : (lushU - nLush) * -b * 2) * 0.5;
              if (nRock) {
                col = pickTone(ROCKY, R.clamp(lv * 0.5 + 0.3, 0, 1), (n - 0.5) * 0.18);
              } else if (nDry > 0.56 + (n - 0.5) * 0.26) {
                col = pickTone(DRY, R.clamp(lv + 0.12, 0, 1), (n - 0.5) * 0.16);
              } else {
                col = pickTone(GRASS, R.clamp(lv, 0, 1), (n - 0.5) * 0.14);
              }
              // 砂の汀
              if (anyShore) {
                let s = 0;
                if (wR) s = Math.max(s, a * 2);
                if (wL) s = Math.max(s, -a * 2);
                if (wD) s = Math.max(s, b * 2);
                if (wU) s = Math.max(s, -b * 2);
                s = R.clamp((s - 0.22) * 1.8, 0, 1);
                if (s > 0.05 && n < s * 1.15) {
                  col = pickTone(SAND, R.clamp(0.4 + (n - 0.5) * 0.6, 0, 1), 0);
                }
              }
              // 崖下の接地影
              let ao = 0;
              if (aoA) ao = Math.max(ao, 0.5 - a);
              if (aoB) ao = Math.max(ao, 0.5 - b);
              ao = R.clamp((ao - 0.62) * 2.4, 0, 1) * 0.42;
              if (ao > 0.02) {
                const rr = col & 255, gg = (col >> 8) & 255, bb2 = (col >> 16) & 255;
                col = pack(
                  Math.round(rr * (1 - ao * 0.55)),
                  Math.round(gg * (1 - ao * 0.5)),
                  Math.round(bb2 * (1 - ao * 0.4))
                );
              }
              // 草の粒・小石・花
              if (!nRock && n > 0.945) {
                const dark = R.hash2(x + 7, y - 3, seed + 19) > 0.5;
                const rr = col & 255, gg = (col >> 8) & 255, bb2 = (col >> 16) & 255;
                const f = dark ? 0.82 : 1.14;
                col = pack(
                  R.clamp(Math.round(rr * f), 0, 255),
                  R.clamp(Math.round(gg * f), 0, 255),
                  R.clamp(Math.round(bb2 * f), 0, 255)
                );
              }
              if (!nRock && nDry <= 0.56 && n > 0.9975) {
                col = FLOWERS[Math.floor(R.hash2(x, y + 5, seed + 29) * FLOWERS.length) % FLOWERS.length];
              }
            }
            put(x, y, col);
          }
        }

        // ── 段差の側面（土の壁） ──────────────────
        for (let lx = 0; lx < TW; lx++) {
          const cb = COL_BOTTOM[lx];
          if (cb < 0) continue;
          const isLeft = lx < TW / 2;
          const wall = isLeft ? wallL : wallR;
          if (wall <= 0) continue;
          const x = bx + lx;
          if (x < 0 || x >= W) continue;
          const gentle = wall <= LEVEL + 1 && !isW;
          const pal = gentle ? (isLeft ? SLOPE : SLOPE_DARK) : isLeft ? DIRT : DIRT_DARK;
          for (let j = 1; j <= wall; j++) {
            const y = by + cb + j;
            if (y < 0) continue;
            if (y >= H) break;
            const n = R.hash2(x, y, seed + 41);
            let t = 0.62 - j * 0.035 + (n - 0.5) * 0.5;
            if (j === 1 && !gentle) t = 0.08;           // 崖の際は暗く締める
            if (isW) t = Math.min(t, 0.2);
            put(x, y, pickTone(pal, R.clamp(t, 0, 0.999), 0));
          }
        }

        // 水面のきらめき候補
        if (isW && depth[i] > 0.22 && R.hash2(tx, ty, seed + 55) > 0.90) {
          sparkles.push({
            x: bx + 4 + Math.floor(R.hash2(tx, ty, seed + 57) * 8),
            y: by + 3 + Math.floor(R.hash2(tx, ty, seed + 59) * 3),
            len: 2 + Math.floor(R.hash2(tx, ty, seed + 61) * 3),
            phase: R.hash2(tx, ty, seed + 63),
          });
        }
      }
    }

    ctx.putImageData(img, 0, 0);

    // ── 遠景のかすみ（上に行くほど空気が白む＝奥行き） ──
    const haze = ctx.createLinearGradient(0, 0, 0, Math.round(H * 0.42));
    haze.addColorStop(0, 'rgba(150,186,190,0.30)');
    haze.addColorStop(0.5, 'rgba(150,186,190,0.10)');
    haze.addColorStop(1, 'rgba(150,186,190,0)');
    ctx.fillStyle = haze;
    ctx.fillRect(0, 0, W, Math.round(H * 0.42));

    function project(tx, ty, h) {
      const hh = h === undefined ? heightOf(Math.round(tx), Math.round(ty)) : h;
      return {
        x: originX + (tx - ty) * HW,
        y: originY + (tx + ty) * HH - hh * LEVEL,
      };
    }

    /** 画面上の矩形を覆うタイル範囲の中から、条件に合うタイルを探す。 */
    function forEachTileInRect(x0, y0, x1, y1, fn) {
      const k0 = Math.floor((y0 - originY) / HH) - MAX_LAND * 2;
      const k1 = Math.ceil((y1 - originY) / HH) + 4;
      const d0 = Math.floor((x0 - originX) / HW) - 2;
      const d1 = Math.ceil((x1 - originX) / HW) + 2;
      for (let k = k0; k <= k1; k++) {
        let dStart = d0;
        if ((((dStart + k) % 2) + 2) % 2 !== 0) dStart++;
        for (let dd = dStart; dd <= d1; dd += 2) {
          const tx = (k + dd) >> 1, ty = (k - dd) >> 1;
          if (!inGrid(tx, ty)) continue;
          fn(tx, ty, at(tx, ty));
        }
      }
    }

    return {
      canvas, width: W, height: H, originX, originY,
      TW, TH, LEVEL, MINT, MAXT,
      heightOf, isWater, project, forEachTileInRect,
      lushAt: (tx, ty) => (inGrid(tx, ty) ? lush[at(tx, ty)] : 0),
      dryAt: (tx, ty) => (inGrid(tx, ty) ? dry[at(tx, ty)] : 0),
      rockyAt: (tx, ty) => (inGrid(tx, ty) ? rocky[at(tx, ty)] === 1 : false),
      forestAt: (tx, ty) => (inGrid(tx, ty) ? forest[at(tx, ty)] : 0),
      depthAt: (tx, ty) => (inGrid(tx, ty) ? depth[at(tx, ty)] : 0),
      inGrid,
      sparkles,
    };
  }

  FT.terrain = { create, TW, TH, LEVEL, WATER_H };
})(window);
