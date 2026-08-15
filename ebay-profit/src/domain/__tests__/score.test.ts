import { describe, expect, it } from 'vitest';
import {
  activeRiskFlags,
  competitionScore,
  computeScore,
  demandScore,
  priceDivergence,
  profitScore,
  riskPenalty,
  turnoverScore,
} from '../score';
import { suggestRiskFlags } from '../risk';
import type { Candidate, ProfitBreakdown, RiskConfig, ScoringConfig } from '../types';

const cfg: ScoringConfig = {
  weights: { demand: 0.22, profit: 0.34, turnover: 0.18, competition: 0.14, risk: 0.12 },
  demand: { sold_count_full: 60, sell_through_full: 1.0 },
  profit: { roi_full: 0.6, profit_jpy_full: 4000, roi_share: 0.5 },
  turnover: { sold_per_month_full: 20 },
  competition: { active_listings_full: 300 },
  risk: {
    penalties: { vero_brand: 60, low_ticket: 20, thin_margin: 25, category_restricted: 50 },
    low_ticket_usd: 15,
    thin_margin_rate: 0.1,
  },
  alerts: { profit_drop_rate: 0.15, min_profit_jpy: 500, min_roi: 0.15 },
};

function candidate(over: Partial<Candidate> = {}): Candidate {
  return {
    id: 'c1',
    title: 'テスト候補',
    sellPriceUsd: 100,
    costJpy: 5000,
    weightG: 400,
    destination: 'US',
    shipMethod: 'epacket_light',
    promoted: false,
    riskFlags: [],
    watch: false,
    createdAt: '2026-01-01T00:00:00.000Z',
    updatedAt: '2026-01-01T00:00:00.000Z',
    ...over,
  };
}

function breakdown(over: Partial<ProfitBreakdown> = {}): ProfitBreakdown {
  return {
    fx: 150,
    revenueJpy: 15000,
    finalValueJpy: 1987.5,
    internationalFeeJpy: 247.5,
    promotedJpy: 0,
    perOrderFixedJpy: 60,
    ebayFeeJpy: 2295,
    payoutFeeJpy: 300,
    costJpy: 5000,
    shippingJpy: 1440,
    miscJpy: 150,
    profitJpy: 5815,
    roi: 5815 / 5000,
    marginRate: 5815 / 15000,
    shipping: { found: true, jpy: 1440, method: 'epacket_light', zone: 'NA' },
    finalValueRate: 0.1325,
    ...over,
  };
}

describe('サブスコア', () => {
  it('需要スコアは販売数と sell-through の平均', () => {
    const c = candidate({
      demand: { soldCount: 30, sellThroughRate: 0.5, source: 'manual' },
    });
    // 30/60=50点, 0.5/1.0=50点 → 50
    expect(demandScore(c, cfg)).toBeCloseTo(50, 6);
  });

  it('需要スコアは基準値超で100に飽和する', () => {
    const c = candidate({ demand: { soldCount: 500, sellThroughRate: 3, source: 'manual' } });
    expect(demandScore(c, cfg)).toBe(100);
  });

  it('需要データが無ければ null', () => {
    expect(demandScore(candidate(), cfg)).toBeNull();
  });

  it('利益スコアは ROI と円のブレンド', () => {
    // roi 0.3 → 50点, 利益2000円 → 50点 → 50
    const s = profitScore(breakdown({ roi: 0.3, profitJpy: 2000 }), cfg);
    expect(s).toBeCloseTo(50, 6);
  });

  it('赤字の利益スコアは0', () => {
    expect(profitScore(breakdown({ roi: -0.5, profitJpy: -3000 }), cfg)).toBe(0);
  });

  it('回転スコアは月換算の販売数', () => {
    const c = candidate({ demand: { soldCount: 30, periodDays: 90, source: 'manual' } });
    // 30/90*30 = 10/月 → 10/20 = 50点
    expect(turnoverScore(c, cfg)).toBeCloseTo(50, 6);
  });

  it('競合スコアは出品中が少ないほど高い', () => {
    expect(competitionScore(candidate({ market: { activeCount: 0 } }), cfg)).toBe(100);
    expect(competitionScore(candidate({ market: { activeCount: 150 } }), cfg)).toBeCloseTo(50, 6);
    expect(competitionScore(candidate({ market: { activeCount: 900 } }), cfg)).toBe(0);
  });
});

describe('リスク', () => {
  it('低単価と薄利は計算から自動でフラグが立つ', () => {
    const flags = activeRiskFlags(
      candidate({ sellPriceUsd: 10 }),
      breakdown({ marginRate: 0.05 }),
      cfg,
    );
    expect(flags).toContain('low_ticket');
    expect(flags).toContain('thin_margin');
  });

  it('健全な候補には自動フラグが立たない', () => {
    const flags = activeRiskFlags(candidate(), breakdown(), cfg);
    expect(flags).toEqual([]);
  });

  it('カテゴリ制限チェックがフラグになる', () => {
    const flags = activeRiskFlags(candidate({ categoryRestricted: true }), breakdown(), cfg);
    expect(flags).toContain('category_restricted');
  });

  it('減点は合計され100で頭打ち', () => {
    expect(riskPenalty(['low_ticket'], cfg)).toBe(20);
    expect(riskPenalty(['low_ticket', 'thin_margin'], cfg)).toBe(45);
    expect(riskPenalty(['vero_brand', 'category_restricted'], cfg)).toBe(100);
  });
});

describe('computeScore', () => {
  it('データが揃った候補はスコアが出る', () => {
    const c = candidate({
      demand: { soldCount: 30, sellThroughRate: 0.5, periodDays: 90, source: 'terapeak-csv' },
      market: { activeCount: 150 },
    });
    const r = computeScore(c, breakdown({ roi: 0.3, profitJpy: 2000 }), cfg);
    // 全サブスコア50、リスク0 → 50
    expect(r.total).toBeCloseTo(50, 6);
    expect(r.missing).toEqual([]);
  });

  it('欠損データは重みごと分母から外れる（0点扱いにしない）', () => {
    const withoutData = computeScore(
      candidate(),
      breakdown({ roi: 0.6, profitJpy: 4000 }),
      cfg,
    );
    // 利益スコアだけが残るので満点
    expect(withoutData.total).toBeCloseTo(100, 6);
    expect(withoutData.missing).toHaveLength(3);
  });

  it('リスク減点が総合スコアを下げる', () => {
    const clean = computeScore(candidate(), breakdown({ roi: 0.6, profitJpy: 4000 }), cfg);
    const risky = computeScore(
      candidate({ riskFlags: ['vero_brand'] }),
      breakdown({ roi: 0.6, profitJpy: 4000 }),
      cfg,
    );
    // 減点60 × 重み0.12 = 7.2
    expect(clean.total - risky.total).toBeCloseTo(7.2, 6);
    expect(risky.activeFlags).toContain('vero_brand');
  });

  it('スコアは0-100に収まる', () => {
    const worst = computeScore(
      candidate({ sellPriceUsd: 5, riskFlags: ['vero_brand'], categoryRestricted: true }),
      breakdown({ roi: -1, profitJpy: -8000, marginRate: -1 }),
      cfg,
    );
    expect(worst.total).toBeGreaterThanOrEqual(0);
    expect(worst.total).toBeLessThanOrEqual(100);
  });
});

describe('priceDivergence', () => {
  it('出品中相場が実売より大幅に高いと警告する', () => {
    const d = priceDivergence(
      candidate({
        demand: { avgSoldPriceUsd: 100, source: 'terapeak-csv' },
        market: { medianUsd: 150 },
      }),
    );
    expect(d?.note).toContain('高い');
  });

  it('値崩れも検出する', () => {
    const d = priceDivergence(
      candidate({
        demand: { avgSoldPriceUsd: 100, source: 'terapeak-csv' },
        market: { medianUsd: 60 },
      }),
    );
    expect(d?.note).toContain('低い');
  });

  it('片方のデータが無ければ null', () => {
    expect(priceDivergence(candidate())).toBeNull();
  });
});

describe('suggestRiskFlags', () => {
  const riskCfg: RiskConfig = {
    rules: [
      { flag: 'vero_brand', label: 'VeRO', hint: '', keywords: ['pokemon', 'ポケモン'] },
      { flag: 'battery', label: '電池', hint: '', keywords: ['battery', 'バッテリー'] },
    ],
  };

  it('タイトルのキーワードからフラグを提案する', () => {
    const s = suggestRiskFlags('Pokemon Card Booster Box', riskCfg);
    expect(s.map((x) => x.flag)).toEqual(['vero_brand']);
    expect(s[0].matched).toContain('pokemon');
  });

  it('日本語キーワードも拾う', () => {
    const s = suggestRiskFlags('モバイルバッテリー 10000mAh', riskCfg);
    expect(s.map((x) => x.flag)).toContain('battery');
  });

  it('該当なしは空配列', () => {
    expect(suggestRiskFlags('Vintage Ceramic Cup', riskCfg)).toEqual([]);
    expect(suggestRiskFlags('', riskCfg)).toEqual([]);
  });
});
