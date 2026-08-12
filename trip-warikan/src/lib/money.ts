/**
 * 金額計算は必ず「最小単位の整数」で行う。
 * 浮動小数のまま足し引きすると 1 円ズレが発生し、
 * 収支の合計が 0 にならなくなって精算アルゴリズムが破綻するため。
 */

/** 主単位 -> 最小単位（例: 12.5 ドル -> 1250） */
export function toMinor(amount: number, decimals: number): number {
  return Math.round(amount * 10 ** decimals);
}

/** 最小単位 -> 主単位（表示・保存用） */
export function fromMinor(minor: number, decimals: number): number {
  return minor / 10 ** decimals;
}

/**
 * 金額を count 人で割る。割り切れない端数は先頭の人から 1 ずつ配る。
 * 戻り値の合計は必ず totalMinor と一致する（1円も消えない・増えない）。
 *
 * 例: 20000 円を 3 人 -> [6667, 6667, 6666]
 */
export function splitEvenly(totalMinor: number, count: number): number[] {
  if (count <= 0) {
    throw new Error('支払い対象者は1人以上必要です');
  }
  const sign = totalMinor < 0 ? -1 : 1;
  const total = Math.abs(totalMinor);
  const base = Math.floor(total / count);
  const remainder = total - base * count;
  return Array.from({ length: count }, (_, i) => sign * (base + (i < remainder ? 1 : 0)));
}
