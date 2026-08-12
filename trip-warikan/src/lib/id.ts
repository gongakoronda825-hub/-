/**
 * ローカル完結アプリなので、端末内で衝突しなければ十分。
 * 時刻＋乱数で十分な一意性が得られる。
 */
export function createId(prefix: string): string {
  const random = Math.random().toString(36).slice(2, 10);
  return `${prefix}_${Date.now().toString(36)}_${random}`;
}
