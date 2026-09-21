/*
 * 乱数とノイズ。地形も植物も恐竜の性格も、全部ここから生やす。
 * シードを固定すれば毎回まったく同じ土地になる（動画の撮り直しに必要）。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});

  /** mulberry32。軽くて質が十分な擬似乱数。 */
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /** 整数座標のハッシュ。0..1 を返す。 */
  function hash2(x, y, seed) {
    let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(seed | 0, 1442695041);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  }

  const smooth = (t) => t * t * (3 - 2 * t);

  /** 値ノイズ。0..1。 */
  function noise2(x, y, seed) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = smooth(x - xi), yf = smooth(y - yi);
    const a = hash2(xi, yi, seed);
    const b = hash2(xi + 1, yi, seed);
    const c = hash2(xi, yi + 1, seed);
    const d = hash2(xi + 1, yi + 1, seed);
    const top = a + (b - a) * xf;
    const bot = c + (d - c) * xf;
    return top + (bot - top) * yf;
  }

  /** フラクタルノイズ。0..1。 */
  function fbm(x, y, seed, octaves, gain) {
    octaves = octaves || 4;
    gain = gain === undefined ? 0.5 : gain;
    let amp = 1, freq = 1, sum = 0, norm = 0;
    for (let i = 0; i < octaves; i++) {
      sum += noise2(x * freq, y * freq, seed + i * 1013) * amp;
      norm += amp;
      amp *= gain;
      freq *= 2;
    }
    return sum / norm;
  }

  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  /** a..b を 0..1 に押し込む。 */
  const smoothstep = (a, b, v) => {
    if (a === b) return v < a ? 0 : 1;
    return smooth(clamp((v - a) / (b - a), 0, 1));
  };

  FT.rng = { mulberry32, hash2, noise2, fbm, clamp, lerp, smoothstep };
})(window);
