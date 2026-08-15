import { cache, handleError, type Req, type Res } from './_lib';

/**
 * 為替（JPY/USD）。キー不要の公開APIを使う。
 * FX_API_URL を環境変数で差し替え可能（レスポンスは { rates: { JPY: number } } 形式想定）。
 */
export default async function handler(_req: Req, res: Res): Promise<void> {
  try {
    const url = process.env.FX_API_URL || 'https://open.er-api.com/v6/latest/USD';
    const r = await fetch(url, { headers: { accept: 'application/json' } });
    if (!r.ok) throw new Error(`為替APIが HTTP ${r.status} を返しました`);
    const data = (await r.json()) as { rates?: Record<string, number> };
    const jpy = data?.rates?.JPY;
    if (typeof jpy !== 'number' || !Number.isFinite(jpy)) {
      throw new Error('為替APIのレスポンスに JPY レートがありません');
    }
    cache(res, 3600);
    res.status(200).json({
      jpyPerUsd: jpy,
      fetchedAt: new Date().toISOString(),
      source: new URL(url).host,
    });
  } catch (e) {
    handleError(res, e);
  }
}
