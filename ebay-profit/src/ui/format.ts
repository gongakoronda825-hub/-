const yenFmt = new Intl.NumberFormat('ja-JP', { maximumFractionDigits: 0 });
const usdFmt = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function yen(n: number | undefined | null): string {
  if (n == null || !Number.isFinite(n)) return '—';
  return `¥${yenFmt.format(Math.round(n))}`;
}

export function usd(n: number | undefined | null): string {
  if (n == null || !Number.isFinite(n)) return '—';
  return `$${usdFmt.format(n)}`;
}

export function pct(n: number | undefined | null, digits = 1): string {
  if (n == null || !Number.isFinite(n)) return '—';
  return `${(n * 100).toFixed(digits)}%`;
}

/** 原価が未入力（0）のときの ROI は「0%」ではなく「—」。0% と誤読させない。 */
export function roiText(roi: number, costJpy: number): string {
  return costJpy > 0 ? pct(roi) : '—';
}

export function num(n: number | undefined | null, digits = 0): string {
  if (n == null || !Number.isFinite(n)) return '—';
  return n.toFixed(digits);
}

export function shortDate(iso: string | undefined | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function signedYen(n: number): string {
  const s = yen(Math.abs(n));
  if (Math.round(n) === 0) return '±¥0';
  return n > 0 ? `+${s}` : `-${s}`;
}
