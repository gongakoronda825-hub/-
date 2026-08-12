import type { CurrencyCode } from '../types';

export type CurrencyInfo = {
  code: CurrencyCode;
  /** 選択画面に出す日本語ラベル */
  label: string;
  /**
   * 小数点以下の桁数（＝最小単位）。
   * 円・ウォン・ドンは補助単位を日常的に使わないため 0。
   * 台湾ドルも実務上は補助単位（分）を使わないため 0 とする。
   */
  decimals: number;
};

export const CURRENCIES: readonly CurrencyInfo[] = [
  { code: 'JPY', label: '日本円', decimals: 0 },
  { code: 'USD', label: '米ドル', decimals: 2 },
  { code: 'KRW', label: '韓国ウォン', decimals: 0 },
  { code: 'TWD', label: '台湾ドル', decimals: 0 },
  { code: 'EUR', label: 'ユーロ', decimals: 2 },
  { code: 'GBP', label: '英ポンド', decimals: 2 },
  { code: 'VND', label: 'ベトナムドン', decimals: 0 },
] as const;

export function currencyInfo(code: CurrencyCode): CurrencyInfo {
  const info = CURRENCIES.find((c) => c.code === code);
  if (!info) {
    throw new Error(`未対応の通貨です: ${code}`);
  }
  return info;
}

export function decimalsFor(code: CurrencyCode): number {
  return currencyInfo(code).decimals;
}

/** 3桁区切り。小数桁は通貨に合わせて必ず固定桁で表示する。 */
function groupDigits(value: number, decimals: number): string {
  const fixed = value.toFixed(decimals);
  const [intPart, fracPart] = fixed.split('.');
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return fracPart ? `${grouped}.${fracPart}` : grouped;
}

/**
 * 最小単位（円・セント）の整数を表示用文字列にする。
 * 例: 18750 (JPY) -> "18,750円" / 3000 (KRW) -> "3,000 KRW"
 */
export function formatMinor(minor: number, code: CurrencyCode): string {
  const { decimals } = currencyInfo(code);
  const major = Math.abs(minor) / 10 ** decimals;
  const body = groupDigits(major, decimals);
  const sign = minor < 0 ? '−' : '';
  return code === 'JPY' ? `${sign}${body}円` : `${sign}${body} ${code}`;
}

/**
 * 収支の表示用。プラスは受け取る側なので明示的に「+」を付ける。
 * 例: 18750 -> "+18,750円" / -1250 -> "−1,250円" / 0 -> "±0円"
 */
export function formatSignedMinor(minor: number, code: CurrencyCode): string {
  if (minor === 0) {
    return `±${formatMinor(0, code)}`;
  }
  return minor > 0 ? `+${formatMinor(minor, code)}` : formatMinor(minor, code);
}
