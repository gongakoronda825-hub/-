/**
 * シード付きの擬似乱数（mulberry32）。
 *
 * 街の小物の置き方はこれで決める。毎回まったく同じ街になることが大事で、
 * 「この路地は逃げやすい」「この角は行き止まり」をプレイヤーが覚えられる
 * （指示書 §13）のは、生成が決定論だから。
 *
 * 住民の判断など「毎回違ってよい」ところでは Math.random() を使う。
 */
export function createRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 配列から1つ選ぶ。 */
export const pick = <T>(random: () => number, items: readonly T[]): T =>
  items[Math.floor(random() * items.length) % items.length];

/** min〜max の実数。 */
export const between = (random: () => number, min: number, max: number): number =>
  min + random() * (max - min);
