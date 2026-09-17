import { describe, expect, it } from 'vitest';
import {
  breakEvenSellPriceUsd,
  computeProfit,
  resolveFinalValueRate,
  resolveShipping,
  resolveZone,
} from '../profit';
import type { Rates, ShippingTable } from '../types';

const rates: Rates = {
  fx_jpy_per_usd: 150,
  ebay: {
    final_value_rate: 0.1325,
    category_final_value_rates: { default: 0.1325, 'Cameras & Photo': 0.0935 },
    international_fee_rate: 0.0165,
    promoted_rate: 0.02,
    per_order_fixed_usd: 0.4,
  },
  payout_fee_rate: 0.02,
  misc_jpy_per_item: 150,
};

const shipping: ShippingTable = {
  zone_of_country: { US: 'NA', DE: 'EU' },
  default_zone: 'OTHER',
  methods: {
    epacket_light: {
      label: 'eパケットライト',
      zones: {
        NA: [
          { max_g: 100, jpy: 720 },
          { max_g: 500, jpy: 1440 },
          { max_g: 2000, jpy: 3960 },
        ],
        EU: [{ max_g: 500, jpy: 1600 }],
        OTHER: [{ max_g: 500, jpy: 1900 }],
      },
    },
    ems: { label: 'EMS', zones: { NA: [{ max_g: 500, jpy: 3900 }] } },
  },
};

describe('resolveZone', () => {
  it('国コードをゾーンに変換する', () => {
    expect(resolveZone(shipping, 'US')).toBe('NA');
    expect(resolveZone(shipping, 'us')).toBe('NA');
    expect(resolveZone(shipping, 'DE')).toBe('EU');
  });

  it('未知の国は default_zone に落ちる', () => {
    expect(resolveZone(shipping, 'ZZ')).toBe('OTHER');
  });
});

describe('resolveShipping', () => {
  it('重量が収まる最小の帯を選ぶ', () => {
    expect(resolveShipping(shipping, 'epacket_light', 'US', 80).jpy).toBe(720);
    expect(resolveShipping(shipping, 'epacket_light', 'US', 100).jpy).toBe(720);
    expect(resolveShipping(shipping, 'epacket_light', 'US', 101).jpy).toBe(1440);
    expect(resolveShipping(shipping, 'epacket_light', 'US', 500).jpy).toBe(1440);
    expect(resolveShipping(shipping, 'epacket_light', 'US', 501).jpy).toBe(3960);
  });

  it('上限超過は found=false で理由を返す', () => {
    const r = resolveShipping(shipping, 'epacket_light', 'US', 2500);
    expect(r.found).toBe(false);
    expect(r.jpy).toBe(0);
    expect(r.reason).toContain('上限');
  });

  it('未知の発送方法・ゾーン・重量ゼロを弾く', () => {
    expect(resolveShipping(shipping, 'unknown', 'US', 100).found).toBe(false);
    expect(resolveShipping(shipping, 'ems', 'DE', 100).found).toBe(false);
    expect(resolveShipping(shipping, 'epacket_light', 'US', 0).found).toBe(false);
  });
});

describe('resolveFinalValueRate', () => {
  it('カテゴリ別料率を優先し、無ければ default', () => {
    expect(resolveFinalValueRate(rates, 'Cameras & Photo')).toBe(0.0935);
    expect(resolveFinalValueRate(rates, 'Unknown Category')).toBe(0.1325);
    expect(resolveFinalValueRate(rates, undefined)).toBe(0.1325);
  });
});

describe('computeProfit', () => {
  it('計画書 2-1 の式どおりに着地利益を出す', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 100,
        costJpy: 5000,
        weightG: 400,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: false,
      },
      rates,
      shipping,
    );

    // 売上 = 100 * 150 = 15000
    expect(p.revenueJpy).toBe(15000);
    // 落札 15000*0.1325 = 1987.5 / 国際 15000*0.0165 = 247.5 / 販促 0 / 固定 0.4*150 = 60
    expect(p.finalValueJpy).toBeCloseTo(1987.5, 6);
    expect(p.internationalFeeJpy).toBeCloseTo(247.5, 6);
    expect(p.promotedJpy).toBe(0);
    expect(p.perOrderFixedJpy).toBeCloseTo(60, 6);
    expect(p.ebayFeeJpy).toBeCloseTo(2295, 6);
    // 入金 15000*0.02 = 300
    expect(p.payoutFeeJpy).toBeCloseTo(300, 6);
    // 送料 400g NA → 1440、雑費 150
    expect(p.shippingJpy).toBe(1440);
    expect(p.miscJpy).toBe(150);
    // 15000 - 2295 - 300 - 5000 - 1440 - 150 = 5815
    expect(p.profitJpy).toBeCloseTo(5815, 6);
    expect(p.roi).toBeCloseTo(5815 / 5000, 10);
    expect(p.marginRate).toBeCloseTo(5815 / 15000, 10);
  });

  it('販促キャンペーン率が乗る', () => {
    const base = {
      sellPriceUsd: 100,
      costJpy: 5000,
      weightG: 400,
      destination: 'US',
      shipMethod: 'epacket_light',
    };
    const off = computeProfit({ ...base, promoted: false }, rates, shipping);
    const on = computeProfit({ ...base, promoted: true }, rates, shipping);
    expect(off.profitJpy - on.profitJpy).toBeCloseTo(15000 * 0.02, 6);
  });

  it('カテゴリ別料率が反映される', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 100,
        costJpy: 5000,
        weightG: 400,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: false,
        category: 'Cameras & Photo',
      },
      rates,
      shipping,
    );
    expect(p.finalValueRate).toBe(0.0935);
    expect(p.finalValueJpy).toBeCloseTo(15000 * 0.0935, 6);
  });

  it('送料の手動指定が料金表より優先される', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 100,
        costJpy: 5000,
        weightG: 400,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: false,
        shippingOverrideJpy: 2500,
      },
      rates,
      shipping,
    );
    expect(p.shippingJpy).toBe(2500);
    expect(p.shipping.reason).toBe('手動指定');
  });

  it('送料が解決できない場合は送料0で計算しつつ found=false を返す', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 100,
        costJpy: 5000,
        weightG: 9000,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: false,
      },
      rates,
      shipping,
    );
    expect(p.shipping.found).toBe(false);
    expect(p.shippingJpy).toBe(0);
  });

  it('為替が変われば利益も変わる', () => {
    const input = {
      sellPriceUsd: 100,
      costJpy: 5000,
      weightG: 400,
      destination: 'US',
      shipMethod: 'epacket_light',
      promoted: false,
    };
    const cheap = computeProfit(input, { ...rates, fx_jpy_per_usd: 130 }, shipping);
    const rich = computeProfit(input, { ...rates, fx_jpy_per_usd: 170 }, shipping);
    expect(rich.profitJpy).toBeGreaterThan(cheap.profitJpy);
  });

  it('原価0でも ROI が NaN/Infinity にならない', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 100,
        costJpy: 0,
        weightG: 400,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: false,
      },
      rates,
      shipping,
    );
    expect(Number.isFinite(p.roi)).toBe(true);
    expect(p.roi).toBe(0);
  });

  it('赤字の候補はマイナスの着地利益になる', () => {
    const p = computeProfit(
      {
        sellPriceUsd: 20,
        costJpy: 5000,
        weightG: 400,
        destination: 'US',
        shipMethod: 'epacket_light',
        promoted: true,
      },
      rates,
      shipping,
    );
    expect(p.profitJpy).toBeLessThan(0);
    expect(p.roi).toBeLessThan(0);
  });
});

describe('breakEvenSellPriceUsd', () => {
  it('逆算した売値で計算すると目標利益に一致する', () => {
    const base = {
      costJpy: 5000,
      weightG: 400,
      destination: 'US',
      shipMethod: 'epacket_light',
      promoted: false,
    };
    const price = breakEvenSellPriceUsd(base, rates, shipping, 0);
    const p = computeProfit({ ...base, sellPriceUsd: price }, rates, shipping);
    expect(p.profitJpy).toBeCloseTo(0, 6);

    const price2 = breakEvenSellPriceUsd(base, rates, shipping, 3000);
    const p2 = computeProfit({ ...base, sellPriceUsd: price2 }, rates, shipping);
    expect(p2.profitJpy).toBeCloseTo(3000, 6);
  });

  it('販促ONだと必要売値が上がる', () => {
    const base = {
      costJpy: 5000,
      weightG: 400,
      destination: 'US',
      shipMethod: 'epacket_light',
    };
    const off = breakEvenSellPriceUsd({ ...base, promoted: false }, rates, shipping, 2000);
    const on = breakEvenSellPriceUsd({ ...base, promoted: true }, rates, shipping, 2000);
    expect(on).toBeGreaterThan(off);
  });
});
