import { getJson } from './http';
import type { MarketData } from '../domain/types';

/**
 * eBay Browse API（出品中のみ）。売れた実績は返らないので、
 * 用途は「競合数」と「現在の出品相場帯」に限定する。
 * 実売データは Terapeak CSV 側から入れること。
 */
export interface BrowseStats {
  query: string;
  activeCount: number;
  medianUsd?: number;
  p25Usd?: number;
  p75Usd?: number;
  sampleSize: number;
  fetchedAt: string;
}

export async function fetchBrowseStats(
  apiBase: string,
  params: { q: string; categoryId?: string; marketplace?: string },
  signal?: AbortSignal,
): Promise<BrowseStats> {
  return getJson<BrowseStats>(
    apiBase,
    'browse',
    { q: params.q, category_ids: params.categoryId, marketplace: params.marketplace },
    signal,
  );
}

export function toMarketData(stats: BrowseStats): MarketData {
  return {
    activeCount: stats.activeCount,
    medianUsd: stats.medianUsd,
    p25Usd: stats.p25Usd,
    p75Usd: stats.p75Usd,
    fetchedAt: stats.fetchedAt,
    query: stats.query,
  };
}
