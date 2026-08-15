import { getJson } from './http';

/**
 * 日本の仕入れ候補サジェスト。公式APIがある媒体のみを扱う。
 * メルカリ・ヤフオク等は公式APIが無いため、ここでは扱わない
 * （手動でURLと価格を貼り付ける運用にする）。
 */
export interface SupplierItem {
  title: string;
  priceJpy: number;
  url: string;
  shop?: string;
  imageUrl?: string;
  source: 'rakuten' | 'yahoo';
}

export interface SupplierSearchResult {
  items: SupplierItem[];
  fetchedAt: string;
}

export async function searchRakuten(
  apiBase: string,
  keyword: string,
  signal?: AbortSignal,
): Promise<SupplierSearchResult> {
  return getJson<SupplierSearchResult>(apiBase, 'rakuten', { keyword }, signal);
}

export async function searchYahoo(
  apiBase: string,
  keyword: string,
  signal?: AbortSignal,
): Promise<SupplierSearchResult> {
  return getJson<SupplierSearchResult>(apiBase, 'yahoo', { keyword }, signal);
}

export async function searchSuppliers(
  apiBase: string,
  keyword: string,
  signal?: AbortSignal,
): Promise<{ items: SupplierItem[]; errors: string[] }> {
  const results = await Promise.allSettled([
    searchRakuten(apiBase, keyword, signal),
    searchYahoo(apiBase, keyword, signal),
  ]);
  const items: SupplierItem[] = [];
  const errors: string[] = [];
  const names = ['楽天市場', 'Yahoo!ショッピング'];
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') items.push(...r.value.items);
    else errors.push(`${names[i]}: ${r.reason?.message ?? '取得失敗'}`);
  });
  items.sort((a, b) => a.priceJpy - b.priceJpy);
  return { items, errors };
}
