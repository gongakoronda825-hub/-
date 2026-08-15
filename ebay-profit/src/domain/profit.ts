import type {
  ProfitBreakdown,
  ProfitInput,
  Rates,
  ShippingResolution,
  ShippingTable,
} from './types';

/**
 * 仕向地 → ゾーンを解決する。未知の国は default_zone に落とす。
 */
export function resolveZone(table: ShippingTable, destination: string): string {
  const code = (destination || '').trim().toUpperCase();
  return table.zone_of_country[code] ?? table.default_zone;
}

/**
 * 発送方法 × ゾーン × 重量 → 送料（円）。
 * 重量が収まる最小の帯を採用する。帯を超える場合は found=false（＝要手動見積り）。
 */
export function resolveShipping(
  table: ShippingTable,
  methodKey: string,
  destination: string,
  weightG: number,
): ShippingResolution {
  const zone = resolveZone(table, destination);
  const method = table.methods[methodKey];

  if (!method) {
    return { found: false, jpy: 0, method: methodKey, zone, reason: '発送方法が料金表にありません' };
  }
  const bands = method.zones[zone];
  if (!bands || bands.length === 0) {
    return { found: false, jpy: 0, method: methodKey, zone, reason: `ゾーン ${zone} の料金が未設定です` };
  }
  if (!Number.isFinite(weightG) || weightG <= 0) {
    return { found: false, jpy: 0, method: methodKey, zone, reason: '重量が未入力です' };
  }

  const sorted = [...bands].sort((a, b) => a.max_g - b.max_g);
  const band = sorted.find((b) => weightG <= b.max_g);
  if (!band) {
    const max = sorted[sorted.length - 1].max_g;
    return {
      found: false,
      jpy: 0,
      method: methodKey,
      zone,
      reason: `重量 ${weightG}g がこの方法の上限 ${max}g を超えています`,
    };
  }
  return { found: true, jpy: band.jpy, method: methodKey, zone, bandMaxG: band.max_g };
}

/** カテゴリ別の落札手数料率。未設定カテゴリは既定値。 */
export function resolveFinalValueRate(rates: Rates, category?: string): number {
  const table = rates.ebay.category_final_value_rates;
  if (category && table && typeof table[category] === 'number') return table[category];
  if (table && typeof table.default === 'number') return table.default;
  return rates.ebay.final_value_rate;
}

/**
 * 着地利益（手取り円）を計算する純関数。計画書 2-1 / 2-2 の式そのまま。
 *
 *   売上_円      = 想定売値_USD × 為替
 *   eBay手数料_円 = 売上_円 × (落札 + 国際取引 + 販促) + 注文固定_USD × 為替
 *   入金手数料_円 = 売上_円 × 入金/決済手数料率
 *   着地利益_円   = 売上 − eBay手数料 − 入金手数料 − 原価 − 送料 − 雑費
 */
export function computeProfit(
  input: ProfitInput,
  rates: Rates,
  shippingTable: ShippingTable,
): ProfitBreakdown {
  const fx = rates.fx_jpy_per_usd;
  const revenueJpy = input.sellPriceUsd * fx;

  const finalValueRate = resolveFinalValueRate(rates, input.category);
  const finalValueJpy = revenueJpy * finalValueRate;
  const internationalFeeJpy = revenueJpy * rates.ebay.international_fee_rate;
  const promotedJpy = input.promoted ? revenueJpy * rates.ebay.promoted_rate : 0;
  const perOrderFixedJpy = rates.ebay.per_order_fixed_usd * fx;
  const ebayFeeJpy = finalValueJpy + internationalFeeJpy + promotedJpy + perOrderFixedJpy;

  const payoutFeeJpy = revenueJpy * rates.payout_fee_rate;

  const shipping =
    input.shippingOverrideJpy != null && Number.isFinite(input.shippingOverrideJpy)
      ? ({
          found: true,
          jpy: input.shippingOverrideJpy,
          method: input.shipMethod,
          zone: resolveZone(shippingTable, input.destination),
          reason: '手動指定',
        } satisfies ShippingResolution)
      : resolveShipping(shippingTable, input.shipMethod, input.destination, input.weightG);

  const shippingJpy = shipping.jpy;
  const costJpy = input.costJpy;
  const miscJpy = rates.misc_jpy_per_item;

  const profitJpy =
    revenueJpy - ebayFeeJpy - payoutFeeJpy - costJpy - shippingJpy - miscJpy;

  const roi = costJpy > 0 ? profitJpy / costJpy : 0;
  const marginRate = revenueJpy > 0 ? profitJpy / revenueJpy : 0;

  return {
    fx,
    revenueJpy,
    finalValueJpy,
    internationalFeeJpy,
    promotedJpy,
    perOrderFixedJpy,
    ebayFeeJpy,
    payoutFeeJpy,
    costJpy,
    shippingJpy,
    miscJpy,
    profitJpy,
    roi,
    marginRate,
    shipping,
    finalValueRate,
  };
}

/**
 * 着地利益が目標額になる想定売値_USD を逆算する（損益分岐・値付け支援）。
 * 手数料は売上に比例するため一次式で解ける。
 */
export function breakEvenSellPriceUsd(
  input: Omit<ProfitInput, 'sellPriceUsd'>,
  rates: Rates,
  shippingTable: ShippingTable,
  targetProfitJpy = 0,
): number {
  const fx = rates.fx_jpy_per_usd;
  const rateSum =
    resolveFinalValueRate(rates, input.category) +
    rates.ebay.international_fee_rate +
    (input.promoted ? rates.ebay.promoted_rate : 0) +
    rates.payout_fee_rate;

  const shipping =
    input.shippingOverrideJpy != null && Number.isFinite(input.shippingOverrideJpy)
      ? input.shippingOverrideJpy
      : resolveShipping(shippingTable, input.shipMethod, input.destination, input.weightG).jpy;

  const fixedJpy =
    rates.ebay.per_order_fixed_usd * fx + input.costJpy + shipping + rates.misc_jpy_per_item;

  const denom = fx * (1 - rateSum);
  if (denom <= 0) return NaN;
  return (targetProfitJpy + fixedJpy) / denom;
}
