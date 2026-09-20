/*
 * 恐竜。骨（折れ線）と太さだけを決めて、円柱シェーディングで塗る。
 * ポーズを関数で作っているので、歩く・止まる・首を下げる、が同じ体から生える。
 *
 * 起動時に全フレームを小さなキャンバスに焼いておき、
 * 実行中は drawImage するだけ。左向きは描画時に反転する。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});
  const P = FT.pixel;
  const R = FT.rng;
  const lerp = R.lerp;

  // パレット: 1=輪郭 2=最暗(奥の脚) 3..7=体(暗→明) 8=目 9=差し色
  const PAL = {
    // 草原の緑に埋もれないよう、恐竜は青みの強い色にしてある
    sauropod: ['', '#101b1e', '#22403f', '#2c5350', '#396864', '#487d76', '#5c948a', '#77ab9e', '#0b0c0a', '#d6e0c0'],
    stego: ['', '#191a22', '#343b46', '#434c58', '#55606c', '#6a7480', '#818b96', '#9aa3ac', '#0b0c0a', '#0b0c0a',
      '#7a3a26', '#a85c33', '#d18b46'],
    raptor: ['', '#1d1109', '#4e2916', '#6b3a1d', '#8a4e26', '#a86431', '#c37e3f', '#dc9c55', '#0b0c0a', '#efd9a8'],
    ptero: ['', '#1a1620', '#40353e', '#584a50', '#6f5e60', '#877672', '#a08d84', '#b9a596', '#0b0c0a', '#c85a3c'],
  };

  const tonesOf = (from, to) => {
    const t = [];
    for (let i = from; i <= to; i++) t.push(i);
    return t;
  };
  const BODY = tonesOf(3, 7);
  const FAR = [2, 2, 3];

  /** 4本脚の1本。phase 0..1 で1歩。 */
  function leg(b, ax, ay, ground, phase, opts) {
    const A = opts.stride;
    const ang = phase * Math.PI * 2;
    const fx = ax + Math.sin(ang) * A;
    const fy = ground - Math.max(0, Math.cos(ang)) * opts.lift;
    const kx = lerp(ax, fx, 0.45) + opts.kneeOut;
    const ky = lerp(ay, ground, 0.55);
    const t = opts.tones;
    P.limb(b, [[ax, ay, opts.r0], [kx, ky, opts.r1], [fx, fy, opts.r2]], t);
    P.limb(b, [[fx - 1.2, fy, opts.r2 * 0.9], [fx + 1.4, fy, opts.r2 * 0.8]], t);
  }

  /** 2本脚（恐竜らしい逆関節）。 */
  function birdLeg(b, ax, ay, ground, phase, opts) {
    const A = opts.stride;
    const ang = phase * Math.PI * 2;
    const fx = ax + Math.sin(ang) * A;
    const fy = ground - Math.max(0, Math.cos(ang)) * opts.lift;
    const kneeX = ax - 0.8 + Math.sin(ang) * A * 0.15;
    const kneeY = lerp(ay, ground, 0.42);
    const ankleX = lerp(kneeX, fx, 0.75) + 0.6;
    const ankleY = lerp(ay, ground, 0.78);
    const t = opts.tones;
    P.limb(b, [[ax, ay, opts.r0], [kneeX, kneeY, opts.r1]], t);
    P.limb(b, [[kneeX, kneeY, opts.r1], [ankleX, ankleY, opts.r2]], t);
    P.limb(b, [[ankleX, ankleY, opts.r2], [fx, fy, opts.r2 * 0.85]], t);
    P.limb(b, [[fx - 1, fy, opts.r2 * 0.8], [fx + 1.6, fy, opts.r2 * 0.7]], t);
  }

  function lerpPts(a, c, t) {
    const out = [];
    for (let i = 0; i < a.length; i++) {
      out.push([lerp(a[i][0], c[i][0], t), lerp(a[i][1], c[i][1], t), lerp(a[i][2], c[i][2], t)]);
    }
    return out;
  }

  // ───────────────────────── 竜脚類（大型草食） ──
  const sauropod = {
    key: 'sauropod',
    w: 52, h: 44, ground: 38,
    anchor: [26, 39],
    shadow: [13, 4],
    speedRange: [2.2, 3.4],
    clips: { walk: 12, idle: 10, graze: 16 },
    draw(b, f) {
      const G = this.ground;
      const walk = f.clip === 'walk';
      const p = f.p;
      const bob = walk ? Math.round(Math.sin(p * Math.PI * 4) * 0.9) : Math.round(Math.sin(p * Math.PI * 2) * 0.5);
      const breathe = f.clip === 'idle' ? Math.sin(p * Math.PI * 2) * 0.35 : 0;
      const neckT = f.clip === 'graze' ? R.clamp(Math.sin(Math.min(p, 0.999) * Math.PI) * 1.9, 0, 1) : 0;
      const sway = walk ? Math.sin(p * Math.PI * 2) : Math.sin(p * Math.PI * 2) * 0.5;

      const st = { stride: 3.0, lift: 2.2, kneeOut: 0.5, r0: 2.9, r1: 2.3, r2: 1.9, tones: FAR };
      // 奥の脚（暗く、少し奥へ）
      leg(b, 21 - 4, 19 + bob - 1, G - 2, walk ? (p + 0.5) % 1 : 0.5, st);
      leg(b, 31 - 4, 18 + bob - 1, G - 2, walk ? p : 0.5, st);

      // 尾から胴体へ一本の背骨
      const spine = [
        [1, 13.5 - sway * 1.4 + bob, 0.5],
        [7, 15.2 - sway * 0.8 + bob, 1.2],
        [13, 16.6 + bob, 2.3],
        [19, 17.2 + bob, 4.4],
        [26, 16.4 + bob + breathe, 5.6],
        [32, 15.2 + bob, 4.6],
      ];
      P.limb(b, spine, BODY);

      // 首と頭
      const neckUp = [
        [32, 15.2 + bob, 4.0], [36, 11.0 + bob, 3.0], [39.5, 6.5 + bob, 2.4], [42, 3.0 + bob, 2.0],
      ];
      const neckDown = [
        [32, 15.2 + bob, 4.0], [36, 21.0 + bob, 3.0], [39, 27.0 + bob, 2.4], [41, 32.5 + bob, 2.0],
      ];
      const neck = lerpPts(neckUp, neckDown, neckT);
      const hx = neck[3][0], hy = neck[3][1];
      const tilt = lerp(-0.15, 1.0, neckT);
      P.limb(b, neck, BODY);
      P.limb(b, [[hx, hy, 1.9], [hx + 3.4, hy + tilt * 1.6, 1.7]], BODY);
      P.limb(b, [[hx + 3.1, hy + tilt * 1.6, 1.4], [hx + 5.4, hy + 0.6 + tilt * 2.0, 1.0]], BODY);
      P.set(b, Math.round(hx + 2.2), Math.round(hy - 1.2 + tilt * 1.2), 8);

      // 手前の脚
      st.tones = BODY;
      st.r0 = 3.2; st.r1 = 2.6; st.r2 = 2.2;
      leg(b, 21, 19 + bob, G, walk ? p : 0.5, st);
      leg(b, 31, 18 + bob, G, walk ? (p + 0.5) % 1 : 0.5, st);

      // 背中の淡い斑
      P.stripes(b, { period: 11, width: 2, slant: 1, map: { 7: 6, 6: 5 } });
    },
  };

  // ───────────────────────── 剣竜（中型草食） ──
  const stego = {
    key: 'stego',
    w: 44, h: 32, ground: 27,
    anchor: [21, 28],
    shadow: [11, 4],
    speedRange: [2.6, 3.8],
    clips: { walk: 12, idle: 10, graze: 16 },
    draw(b, f) {
      const G = this.ground;
      const walk = f.clip === 'walk';
      const p = f.p;
      const bob = walk ? Math.round(Math.sin(p * Math.PI * 4) * 0.7) : 0;
      const breathe = f.clip === 'idle' ? Math.sin(p * Math.PI * 2) * 0.3 : 0;
      const neckT = f.clip === 'graze' ? R.clamp(Math.sin(Math.min(p, 0.999) * Math.PI) * 1.9, 0, 1) : 0;
      const sway = Math.sin(p * Math.PI * 2);

      const st = { stride: 1.9, lift: 1.5, kneeOut: 0.4, r0: 2.2, r1: 1.8, r2: 1.5, tones: FAR };
      leg(b, 15 - 4, 16.5 + bob - 1, G - 2, walk ? (p + 0.5) % 1 : 0.5, st);
      leg(b, 24 - 4, 16.0 + bob - 1, G - 2, walk ? p : 0.5, st);

      const spine = [
        [2, 14.0 - sway * 1.0 + bob, 0.7],
        [7, 13.2 - sway * 0.5 + bob, 1.5],
        [12, 13.4 + bob, 2.8],
        [18, 12.8 + bob + breathe, 4.4],
        [24, 13.6 + bob, 3.2],
      ];
      P.limb(b, spine, BODY);

      const neckUp = [[24, 13.6 + bob, 2.8], [27.5, 12.6 + bob, 2.2], [30, 12.6 + bob, 1.8]];
      const neckDown = [[24, 13.6 + bob, 2.8], [28, 16.5 + bob, 2.2], [30, 20.5 + bob, 1.8]];
      const neck = lerpPts(neckUp, neckDown, neckT);
      P.limb(b, neck, BODY);
      const hx = neck[2][0], hy = neck[2][1];
      P.limb(b, [[hx, hy, 1.8], [hx + 3.0, hy + 0.4 + neckT * 1.2, 1.5]], BODY);
      P.limb(b, [[hx + 2.8, hy + 0.5 + neckT, 1.2], [hx + 4.6, hy + 1.1 + neckT * 1.4, 0.8]], BODY);
      P.set(b, Math.round(hx + 1.4), Math.round(hy - 1 + neckT), 8);

      // 背板（左右2列に見えるよう、大小を交互に）
      const plates = 9;
      for (let i = 0; i < plates; i++) {
        const t = i / (plates - 1);
        const sx = lerp(6, 23.5, t);
        const hump = Math.sin(Math.PI * Math.min(1, t * 1.05));
        const top = 13.4 + bob - hump * 2.6;
        const size = (2.0 + hump * 3.8) * (i % 2 === 0 ? 1 : 0.76);
        const lean = i % 2 === 0 ? -0.7 : 0.9;
        P.poly(b, [
          [sx - size * 0.62, top],
          [sx + lean, top - size],
          [sx + size * 0.62, top],
        ], (x, y) => (y < top - size * 0.62 ? 12 : y < top - size * 0.28 ? 11 : 10));
      }
      // 尾のスパイク
      P.poly(b, [[3.5, 14 + bob], [1.0, 10.5 + bob], [5.0, 13 + bob]], 12);
      P.poly(b, [[5.5, 14.5 + bob], [4.0, 10.5 + bob], [7.5, 13.5 + bob]], 11);

      const st2 = { stride: 1.9, lift: 1.5, kneeOut: 0.4, r0: 2.6, r1: 2.1, r2: 1.8, tones: BODY };
      leg(b, 15, 16.5 + bob, G, walk ? p : 0.5, st2);
      leg(b, 24, 16.0 + bob, G, walk ? (p + 0.5) % 1 : 0.5, st2);
    },
  };

  // ───────────────────────── 小型恐竜（走る） ──
  const raptor = {
    key: 'raptor',
    w: 32, h: 26, ground: 21,
    anchor: [15, 22],
    shadow: [6, 2],
    speedRange: [5.5, 8.0],
    clips: { walk: 10, run: 8, idle: 10, look: 12 },
    draw(b, f) {
      const G = this.ground;
      const p = f.p;
      const run = f.clip === 'run';
      const walk = f.clip === 'walk' || run;
      const bob = run ? Math.round(Math.sin(p * Math.PI * 2) * 1.3)
        : walk ? Math.round(Math.sin(p * Math.PI * 4) * 0.6) : 0;
      const lookT = f.clip === 'look' ? Math.sin(Math.min(p, 0.999) * Math.PI) : 0;
      const tailSway = Math.sin(p * Math.PI * 2) * (run ? 1.5 : 0.8);
      const lean = run ? 1.2 : 0; // 走るときは前傾

      const st = {
        stride: run ? 3.4 : 2.1, lift: run ? 2.8 : 1.5, kneeOut: 0,
        r0: 1.8, r1: 1.3, r2: 0.95, tones: FAR,
      };
      birdLeg(b, 14 - 2.5, 11.5 + bob - 1, G - 1.5, (p + 0.5) % 1, st);

      // 尾 → 胴
      const spine = [
        [1, 6.6 + tailSway - lean + bob, 0.6],
        [6, 8.0 + tailSway * 0.5 - lean * 0.6 + bob, 1.2],
        [11, 9.0 + bob, 2.4],
        [15, 9.2 + bob, 3.1],
        [19, 8.4 - lean * 0.4 + bob, 2.4],
      ];
      P.limb(b, spine, BODY);

      // 首と頭
      const neck = lerpPts(
        [[19, 8.4 + bob, 1.9], [21, 5.8 - lean + bob, 1.5], [22.5, 4.4 - lean + bob, 1.4]],
        [[19, 8.4 + bob, 1.9], [21.5, 7.6 + bob, 1.5], [23.5, 8.6 + bob, 1.4]],
        lookT
      );
      P.limb(b, neck, BODY);
      const hx = neck[2][0], hy = neck[2][1];
      P.limb(b, [[hx, hy, 1.6], [hx + 2.8, hy + 0.4 + lookT * 0.5, 1.2]], BODY);
      P.limb(b, [[hx + 2.6, hy + 0.5 + lookT * 0.5, 1.0], [hx + 4.6, hy + 1.1 + lookT * 0.8, 0.6]], BODY);
      // 前肢
      P.limb(b, [[18, 9.6 + bob, 0.9], [20.4, 11.6 + bob, 0.6]], [3, 4]);

      st.tones = BODY;
      st.r0 = 2.0; st.r1 = 1.4; st.r2 = 1.05;
      birdLeg(b, 14, 11.5 + bob, G, p, st);

      P.stripes(b, { period: 9, width: 2, slant: 0, map: { 7: 6, 6: 5, 5: 4 } });
      P.set(b, Math.round(hx + 1.1), Math.round(hy - 0.7), 8);
    },
  };

  // ───────────────────────── 翼竜（空を横切る／真上から） ──
  const ptero = {
    key: 'ptero',
    w: 36, h: 32, ground: 16,
    anchor: [18, 16],
    shadow: [7, 3],
    speedRange: [16, 22],
    clips: { fly: 10 },
    draw(b, f) {
      const p = f.p;
      const flap = Math.sin(p * Math.PI * 2);
      const span = 10.5 + flap * 3.6;
      const cy = 16 - flap * 0.7;
      const T = [3, 4, 5, 6, 7];

      // 翼（真上から見た後退翼。羽ばたきで幅が変わる）
      for (const s of [-1, 1]) {
        const tip = cy + s * span;
        P.poly(b, [
          [21, cy + s * 1.8],
          [16, cy + s * span * 0.78],
          [11.5, tip],
          [9.5, tip - s * 0.9],
          [12.5, cy + s * span * 0.42],
          [14, cy + s * 2.6],
        ], (x, y) => {
          const k = Math.abs(y - cy) / (span || 1);
          return k > 0.76 ? 3 : k > 0.42 ? 4 : 5;
        });
        // 翼の前縁（指の骨）を明るく
        P.limb(b, [[21, cy + s * 1.8, 0.6], [16, cy + s * span * 0.78, 0.55], [11.6, tip, 0.5]], [6, 7]);
        // 後ろ脚
        P.limb(b, [[11, cy + s * 1.2, 0.6], [7, cy + s * 2.4, 0.4]], [3, 4]);
      }
      // 胴・首・頭・くちばし
      P.limb(b, [[9, cy, 1.0], [14, cy, 2.0], [19, cy, 1.6]], T);
      P.limb(b, [[19, cy, 1.3], [23, cy, 1.2]], T);
      P.limb(b, [[23, cy, 1.2], [26, cy, 1.0]], T);
      P.limb(b, [[26, cy, 0.8], [31, cy + 0.2, 0.4]], T);
      // 後ろへ伸びる鶏冠
      P.poly(b, [[25, cy - 1.0], [21.5, cy - 3.6], [25.5, cy - 0.4]], 9);
      P.set(b, 26, Math.round(cy - 1), 8);
    },
  };

  const DEFS = { sauropod, stego, raptor, ptero };

  /** 全種・全クリップのフレームを焼く。 */
  function bakeAll() {
    const out = {};
    for (const key of Object.keys(DEFS)) {
      const def = DEFS[key];
      const pal = PAL[key];
      const clips = {};
      for (const clipName of Object.keys(def.clips)) {
        const n = def.clips[clipName];
        const frames = [];
        for (let i = 0; i < n; i++) {
          const b = P.buf(def.w, def.h);
          def.draw(b, { clip: clipName, p: i / n, i });
          P.outline(b, 1);
          frames.push(P.toCanvas(b, pal));
        }
        clips[clipName] = frames;
      }
      out[key] = {
        key,
        clips,
        w: def.w, h: def.h,
        anchor: def.anchor,
        shadow: def.shadow,
        speedRange: def.speedRange,
      };
    }
    return out;
  }

  FT.species = { bakeAll, DEFS, PAL };
})(window);
