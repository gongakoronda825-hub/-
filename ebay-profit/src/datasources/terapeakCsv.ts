import Papa from 'papaparse';
import type { Candidate } from '../domain/types';

/**
 * Terapeak（Seller Hub → Product Research）の検索結果を画面から CSV エクスポートした
 * ファイルを取り込む。eBay 側で列名が変わっても壊れないよう、列マッピングは
 * 「推測 → UIで手直し」の2段構えにしてある。
 * ※ スクレイピングは行わない。ユーザーが手元にダウンロードした CSV のみを読む。
 */

export type CanonicalField =
  | 'title'
  | 'avgSoldPriceUsd'
  | 'soldCount'
  | 'sellThroughRate'
  | 'category';

export type ColumnMapping = Partial<Record<CanonicalField, string>>;

export interface ParsedCsv {
  headers: string[];
  rows: Record<string, string>[];
}

export const FIELD_LABELS: Record<CanonicalField, string> = {
  title: '商品名 / 検索キーワード',
  avgSoldPriceUsd: '平均売値（USD）',
  soldCount: '販売数',
  sellThroughRate: 'sell-through率',
  category: 'カテゴリ',
};

export const REQUIRED_FIELDS: CanonicalField[] = ['title'];

/** 列名の揺れを吸収するための同義語辞書（小文字・記号除去して比較） */
const SYNONYMS: Record<CanonicalField, string[]> = {
  title: ['product name', 'productname', 'title', 'item title', 'search term', 'keyword', '商品名', 'キーワード'],
  avgSoldPriceUsd: [
    'avg sold price',
    'average sold price',
    'avg price',
    'average sale price',
    'avg selling price',
    'median price',
    '平均売値',
    '平均落札価格',
  ],
  soldCount: [
    'total sold',
    'sold count',
    'quantity sold',
    'items sold',
    'sold quantity',
    'sold',
    '販売数',
    '売れた数',
  ],
  sellThroughRate: ['sell through', 'sell-through', 'sell through rate', 'str', '売却率', '販売率'],
  category: ['category', 'category name', 'leaf category', 'カテゴリ'],
};

function normalizeHeader(h: string): string {
  return h
    .toLowerCase()
    .replace(/[_\-.()%$]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** 見出し行から列マッピングを推測する */
export function guessMapping(headers: string[]): ColumnMapping {
  const mapping: ColumnMapping = {};
  const normalized = headers.map((h) => ({ raw: h, norm: normalizeHeader(h) }));

  for (const field of Object.keys(SYNONYMS) as CanonicalField[]) {
    const syns = SYNONYMS[field].map(normalizeHeader);
    // 完全一致 → 前方一致 → 部分一致 の順で拾う
    const exact = normalized.find((h) => syns.includes(h.norm));
    if (exact) {
      mapping[field] = exact.raw;
      continue;
    }
    const partial = normalized.find((h) => syns.some((s) => h.norm.includes(s)));
    if (partial) mapping[field] = partial.raw;
  }
  return mapping;
}

/** "$1,234.56" / "1 234,56" / "¥1,200" → 数値。解釈できなければ undefined。 */
export function parseNumber(raw: string | undefined | null): number | undefined {
  if (raw == null) return undefined;
  const s = String(raw).trim();
  if (!s) return undefined;
  const cleaned = s.replace(/[^0-9.\-]/g, '');
  if (!cleaned || cleaned === '-' || cleaned === '.') return undefined;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : undefined;
}

/** "83%" → 0.83 / "0.83" → 0.83 / "83" → 0.83（%記号なしでも1超なら%とみなす） */
export function parseRate(raw: string | undefined | null): number | undefined {
  if (raw == null) return undefined;
  const s = String(raw).trim();
  if (!s) return undefined;
  const n = parseNumber(s);
  if (n == null) return undefined;
  if (s.includes('%')) return n / 100;
  return n > 1 ? n / 100 : n;
}

export function parseCsvText(text: string): ParsedCsv {
  const result = Papa.parse<Record<string, string>>(text, {
    header: true,
    skipEmptyLines: 'greedy',
    transformHeader: (h) => h.trim(),
  });
  const rows = (result.data || []).filter(
    (r) => r && Object.values(r).some((v) => String(v ?? '').trim() !== ''),
  );
  const headers = (result.meta?.fields ?? []).filter((h) => h && h.trim() !== '');
  return { headers, rows };
}

export function parseCsvFile(file: File): Promise<ParsedCsv> {
  return file.text().then(parseCsvText);
}

export interface ImportDefaults {
  costJpy: number;
  weightG: number;
  destination: string;
  shipMethod: string;
  promoted: boolean;
  /** Terapeak の検索期間（日）。回転スコアの分母になる。 */
  periodDays: number;
}

export interface ImportRowResult {
  candidate?: Candidate;
  skipped?: string;
  rowIndex: number;
}

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `c_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

/**
 * CSV 行 → 候補。平均売値が取れていれば想定売値USDの初期値にする（無ければ0で手入力待ち）。
 */
export function rowsToCandidates(
  rows: Record<string, string>[],
  mapping: ColumnMapping,
  defaults: ImportDefaults,
  now = new Date().toISOString(),
): ImportRowResult[] {
  return rows.map((row, rowIndex) => {
    const title = mapping.title ? String(row[mapping.title] ?? '').trim() : '';
    if (!title) return { rowIndex, skipped: '商品名が空の行' };

    const avgSoldPriceUsd = mapping.avgSoldPriceUsd
      ? parseNumber(row[mapping.avgSoldPriceUsd])
      : undefined;
    const soldCount = mapping.soldCount ? parseNumber(row[mapping.soldCount]) : undefined;
    const sellThroughRate = mapping.sellThroughRate
      ? parseRate(row[mapping.sellThroughRate])
      : undefined;
    const category = mapping.category ? String(row[mapping.category] ?? '').trim() : undefined;

    const candidate: Candidate = {
      id: newId(),
      title,
      category: category || undefined,
      keyword: title,
      sellPriceUsd: avgSoldPriceUsd ?? 0,
      costJpy: defaults.costJpy,
      weightG: defaults.weightG,
      destination: defaults.destination,
      shipMethod: defaults.shipMethod,
      promoted: defaults.promoted,
      demand: {
        avgSoldPriceUsd,
        soldCount,
        sellThroughRate,
        periodDays: defaults.periodDays,
        source: 'terapeak-csv',
        fetchedAt: now,
      },
      riskFlags: [],
      watch: false,
      createdAt: now,
      updatedAt: now,
    };
    return { rowIndex, candidate };
  });
}
