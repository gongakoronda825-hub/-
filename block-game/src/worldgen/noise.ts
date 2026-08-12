/**
 * シード付きのノイズ。外部ライブラリを増やしたくないので小さく自前で持つ。
 *
 * 地形も木も「(seed, x, z) の純関数」でなければならない。チャンクの生成順で
 * 結果が変わると、同じ場所を離れて戻ったときに地形が食い違う。
 */

/** 32bit の整数ハッシュ。0〜1 を返す。 */
export function hash2(seed: number, x: number, z: number): number {
  let h = seed ^ Math.imul(x | 0, 0x27d4eb2d) ^ Math.imul(z | 0, 0x165667b1);
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 13), 0x297a2d39);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

/** 同じ座標から複数の独立した乱数が欲しいとき用。 */
export const hash3 = (seed: number, x: number, z: number, salt: number): number =>
  hash2(seed ^ Math.imul(salt + 1, 0x9e3779b9), x, z);

const fade = (t: number): number => t * t * t * (t * (t * 6 - 15) + 10);
const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

/** 格子点の勾配（単位ベクトル）を座標から決める。 */
function gradient(seed: number, ix: number, iz: number, dx: number, dz: number): number {
  const angle = hash2(seed, ix, iz) * Math.PI * 2;
  return Math.cos(angle) * dx + Math.sin(angle) * dz;
}

/**
 * 2D パーリンノイズ。おおむね -1〜1。
 */
export function perlin2(seed: number, x: number, z: number): number {
  const x0 = Math.floor(x);
  const z0 = Math.floor(z);
  const x1 = x0 + 1;
  const z1 = z0 + 1;

  const dx = x - x0;
  const dz = z - z0;
  const u = fade(dx);
  const v = fade(dz);

  const n00 = gradient(seed, x0, z0, dx, dz);
  const n10 = gradient(seed, x1, z0, dx - 1, dz);
  const n01 = gradient(seed, x0, z1, dx, dz - 1);
  const n11 = gradient(seed, x1, z1, dx - 1, dz - 1);

  return lerp(lerp(n00, n10, u), lerp(n01, n11, u), v);
}

/**
 * fBm（複数オクターブの合成）。
 * 低周波の大きな起伏に、振幅を半分ずつ落としながら細かい凹凸を重ねる。
 * 戻り値はおおむね -1〜1 に正規化してある。
 */
export function fbm2(seed: number, x: number, z: number, octaves: number, scale: number): number {
  let amplitude = 1;
  let frequency = 1 / scale;
  let sum = 0;
  let norm = 0;

  for (let i = 0; i < octaves; i++) {
    sum += perlin2(seed + i * 1013, x * frequency, z * frequency) * amplitude;
    norm += amplitude;
    amplitude *= 0.5;
    frequency *= 2;
  }

  return sum / norm;
}
