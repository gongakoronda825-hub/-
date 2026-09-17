import { cache, fail, handleError, param, requireEnv, type Req, type Res } from './_lib';

/**
 * 楽天市場 商品検索API プロキシ（公式API・利用規約の範囲内）。
 * 必要な環境変数: RAKUTEN_APP_ID（アフィリエイトIDは任意で RAKUTEN_AFFILIATE_ID）
 */
interface RakutenItem {
  itemName: string;
  itemPrice: number;
  itemUrl: string;
  shopName?: string;
  mediumImageUrls?: { imageUrl: string }[];
}

export default async function handler(req: Req, res: Res): Promise<void> {
  try {
    const keyword = param(req, 'keyword');
    if (!keyword) {
      fail(res, 400, 'keyword が必要です');
      return;
    }
    const appId = requireEnv('RAKUTEN_APP_ID');

    const qs = new URLSearchParams({
      applicationId: appId,
      keyword,
      hits: '20',
      sort: '+itemPrice',
      format: 'json',
    });
    const affiliateId = process.env.RAKUTEN_AFFILIATE_ID;
    if (affiliateId) qs.set('affiliateId', affiliateId);

    const r = await fetch(
      `https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601?${qs}`,
      { headers: { accept: 'application/json' } },
    );
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`楽天APIが HTTP ${r.status}: ${text.slice(0, 200)}`);
    }
    const data = (await r.json()) as { Items?: { Item: RakutenItem }[] };

    const items = (data.Items ?? []).map(({ Item }) => ({
      title: Item.itemName,
      priceJpy: Item.itemPrice,
      url: Item.itemUrl,
      shop: Item.shopName,
      imageUrl: Item.mediumImageUrls?.[0]?.imageUrl,
      source: 'rakuten' as const,
    }));

    cache(res, 900);
    res.status(200).json({ items, fetchedAt: new Date().toISOString() });
  } catch (e) {
    handleError(res, e);
  }
}
