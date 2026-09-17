import { cache, fail, handleError, param, requireEnv, type Req, type Res } from './_lib';

/**
 * Yahoo!ショッピング 商品検索API プロキシ（公式API・利用規約の範囲内）。
 * ※ ヤフオク（オークション）はここでは扱わない。公式の商品検索APIが無く、
 *    自動アクセスも規約で認められていないため、手動貼り付け運用にする。
 * 必要な環境変数: YAHOO_APP_ID（Client ID）
 */
interface YahooHit {
  name: string;
  url: string;
  price: number;
  seller?: { name?: string };
  image?: { medium?: string };
}

export default async function handler(req: Req, res: Res): Promise<void> {
  try {
    const keyword = param(req, 'keyword');
    if (!keyword) {
      fail(res, 400, 'keyword が必要です');
      return;
    }
    const appId = requireEnv('YAHOO_APP_ID');

    const qs = new URLSearchParams({
      appid: appId,
      query: keyword,
      results: '20',
      sort: '+price',
    });

    const r = await fetch(
      `https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?${qs}`,
      { headers: { accept: 'application/json' } },
    );
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`Yahoo!ショッピングAPIが HTTP ${r.status}: ${text.slice(0, 200)}`);
    }
    const data = (await r.json()) as { hits?: YahooHit[] };

    const items = (data.hits ?? []).map((h) => ({
      title: h.name,
      priceJpy: h.price,
      url: h.url,
      shop: h.seller?.name,
      imageUrl: h.image?.medium,
      source: 'yahoo' as const,
    }));

    cache(res, 900);
    res.status(200).json({ items, fetchedAt: new Date().toISOString() });
  } catch (e) {
    handleError(res, e);
  }
}
