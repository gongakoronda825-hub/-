import { getJson } from './http';

export interface FxResult {
  jpyPerUsd: number;
  fetchedAt: string;
  source: string;
}

/** 為替（JPY/USD）を取得する。失敗時は呼び出し側で手動値のまま続行させる。 */
export async function fetchFx(apiBase: string, signal?: AbortSignal): Promise<FxResult> {
  return getJson<FxResult>(apiBase, 'fx', {}, signal);
}
