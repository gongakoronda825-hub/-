import { cache, fail, handleError, param, percentile, requireEnv, type Req, type Res } from './_lib';

/**
 * eBay Browse API プロキシ。
 * - 返るのは「出品中」の商品のみ（売れた実績は返らない仕様）。競合数と相場帯の把握に使う。
 * - OAuth は client credentials（application token）。キーはサーバー側の環境変数のみ。
 *
 * 必要な環境変数:
 *   EBAY_CLIENT_ID      … App ID (Client ID)
 *   EBAY_CLIENT_SECRET  … Cert ID (Client Secret)
 *   EBAY_ENV            … "production"（既定）または "sandbox"
 */

interface CachedToken {
  token: string;
  expiresAt: number;
}
let tokenCache: CachedToken | null = null;

function hosts(env: string) {
  const sandbox = env === 'sandbox';
  return {
    auth: sandbox ? 'https://api.sandbox.ebay.com' : 'https://api.ebay.com',
    api: sandbox ? 'https://api.sandbox.ebay.com' : 'https://api.ebay.com',
  };
}

async function getToken(): Promise<string> {
  const now = Date.now();
  if (tokenCache && tokenCache.expiresAt > now + 60_000) return tokenCache.token;

  const clientId = requireEnv('EBAY_CLIENT_ID');
  const clientSecret = requireEnv('EBAY_CLIENT_SECRET');
  const env = process.env.EBAY_ENV || 'production';

  const basic = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
  const body = new URLSearchParams({
    grant_type: 'client_credentials',
    scope: 'https://api.ebay.com/oauth/api_scope',
  });

  const r = await fetch(`${hosts(env).auth}/identity/v1/oauth2/token`, {
    method: 'POST',
    headers: {
      authorization: `Basic ${basic}`,
      'content-type': 'application/x-www-form-urlencoded',
    },
    body,
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`eBay OAuth が HTTP ${r.status}: ${text.slice(0, 200)}`);
  }
  const data = (await r.json()) as { access_token: string; expires_in: number };
  tokenCache = {
    token: data.access_token,
    expiresAt: now + (data.expires_in ?? 7200) * 1000,
  };
  return tokenCache.token;
}

interface ItemSummary {
  price?: { value?: string; currency?: string };
}

export default async function handler(req: Req, res: Res): Promise<void> {
  try {
    const q = param(req, 'q');
    const categoryIds = param(req, 'category_ids');
    const marketplace = param(req, 'marketplace') || 'EBAY_US';
    if (!q && !categoryIds) {
      fail(res, 400, 'q または category_ids が必要です');
      return;
    }

    const token = await getToken();
    const env = process.env.EBAY_ENV || 'production';

    const qs = new URLSearchParams({ limit: '200' });
    if (q) qs.set('q', q);
    if (categoryIds) qs.set('category_ids', categoryIds);
    qs.set('filter', 'buyingOptions:{FIXED_PRICE|AUCTION}');

    const r = await fetch(`${hosts(env).api}/buy/browse/v1/item_summary/search?${qs}`, {
      headers: {
        authorization: `Bearer ${token}`,
        'X-EBAY-C-MARKETPLACE-ID': marketplace,
        accept: 'application/json',
      },
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error(`Browse API が HTTP ${r.status}: ${text.slice(0, 200)}`);
    }
    const data = (await r.json()) as { total?: number; itemSummaries?: ItemSummary[] };

    const currency = marketplace === 'EBAY_US' ? 'USD' : undefined;
    const prices = (data.itemSummaries ?? [])
      .filter((it) => !currency || it.price?.currency === currency)
      .map((it) => Number(it.price?.value))
      .filter((n) => Number.isFinite(n) && n > 0)
      .sort((a, b) => a - b);

    cache(res, 900);
    res.status(200).json({
      query: q ?? `category:${categoryIds}`,
      activeCount: data.total ?? prices.length,
      medianUsd: percentile(prices, 0.5),
      p25Usd: percentile(prices, 0.25),
      p75Usd: percentile(prices, 0.75),
      sampleSize: prices.length,
      fetchedAt: new Date().toISOString(),
    });
  } catch (e) {
    handleError(res, e);
  }
}
