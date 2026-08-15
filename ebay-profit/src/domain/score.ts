import type {
  Candidate,
  ProfitBreakdown,
  RiskFlag,
  ScoreResult,
  ScoringConfig,
} from './types';

export function clamp(v: number, min: number, max: number): number {
  if (!Number.isFinite(v)) return min;
  return Math.min(max, Math.max(min, v));
}

/** 0..full を 0..100 に線形正規化し、full 超は 100 で飽和 */
function saturate(value: number | undefined, full: number): number | null {
  if (value == null || !Number.isFinite(value)) return null;
  if (full <= 0) return 0;
  return clamp((value / full) * 100, 0, 100);
}

/** 需要スコア：販売数と sell-through 率の平均（片方しか無ければその値） */
export function demandScore(c: Candidate, cfg: ScoringConfig): number | null {
  const d = c.demand;
  if (!d) return null;
  const bySold = saturate(d.soldCount, cfg.demand.sold_count_full);
  const byStr = saturate(d.sellThroughRate, cfg.demand.sell_through_full);
  const parts = [bySold, byStr].filter((v): v is number => v != null);
  if (parts.length === 0) return null;
  return parts.reduce((a, b) => a + b, 0) / parts.length;
}

/** 利益スコア：ROI と 1個利益円の加重合成 */
export function profitScore(p: ProfitBreakdown, cfg: ScoringConfig): number {
  const byRoi = saturate(Math.max(p.roi, 0), cfg.profit.roi_full) ?? 0;
  const byYen = saturate(Math.max(p.profitJpy, 0), cfg.profit.profit_jpy_full) ?? 0;
  const share = clamp(cfg.profit.roi_share, 0, 1);
  return byRoi * share + byYen * (1 - share);
}

/** 回転スコア：販売数 ÷ 集計期間 を月あたりに換算 */
export function turnoverScore(c: Candidate, cfg: ScoringConfig): number | null {
  const d = c.demand;
  if (!d || d.soldCount == null || !d.periodDays || d.periodDays <= 0) return null;
  const perMonth = (d.soldCount / d.periodDays) * 30;
  return saturate(perMonth, cfg.turnover.sold_per_month_full);
}

/** 競合スコア：出品中件数が少ないほど高い */
export function competitionScore(c: Candidate, cfg: ScoringConfig): number | null {
  const n = c.market?.activeCount;
  if (n == null || !Number.isFinite(n)) return null;
  const full = cfg.competition.active_listings_full;
  if (full <= 0) return 0;
  return clamp(100 - (n / full) * 100, 0, 100);
}

/** 立っているリスクフラグ（手動＋計算由来の自動フラグ） */
export function activeRiskFlags(
  c: Candidate,
  p: ProfitBreakdown,
  cfg: ScoringConfig,
): RiskFlag[] {
  const flags: RiskFlag[] = [...c.riskFlags];
  if (c.categoryRestricted) flags.push('category_restricted');
  if (c.sellPriceUsd > 0 && c.sellPriceUsd < cfg.risk.low_ticket_usd) flags.push('low_ticket');
  if (p.marginRate < cfg.risk.thin_margin_rate) flags.push('thin_margin');
  return Array.from(new Set(flags));
}

/** リスク減点：立っているフラグの減点合計（0-100 で頭打ち） */
export function riskPenalty(flags: RiskFlag[], cfg: ScoringConfig): number {
  const sum = flags.reduce((acc, f) => acc + (cfg.risk.penalties[f] ?? 0), 0);
  return clamp(sum, 0, 100);
}

/**
 * 総合スコア。
 *   総合 = 需要×w1 + 利益×w2 + 回転×w3 + 競合×w4 − リスク減点×w5
 * データ欠損のサブスコアは重みごと分母から外す（欠損を 0 点扱いにして
 * 不当に沈めない）。リスク減点は常に効く。
 */
export function computeScore(
  c: Candidate,
  p: ProfitBreakdown,
  cfg: ScoringConfig,
): ScoreResult {
  const missing: string[] = [];

  const demand = demandScore(c, cfg);
  if (demand == null) missing.push('需要データ（Terapeak/手動）');
  const turnover = turnoverScore(c, cfg);
  if (turnover == null) missing.push('回転データ（販売数/期間）');
  const competition = competitionScore(c, cfg);
  if (competition == null) missing.push('競合データ（Browse API）');

  const profit = profitScore(p, cfg);

  const w = cfg.weights;
  const positives: { value: number; weight: number }[] = [
    { value: profit, weight: w.profit },
  ];
  if (demand != null) positives.push({ value: demand, weight: w.demand });
  if (turnover != null) positives.push({ value: turnover, weight: w.turnover });
  if (competition != null) positives.push({ value: competition, weight: w.competition });

  const weightSum = positives.reduce((a, b) => a + b.weight, 0);
  const positiveScore =
    weightSum > 0 ? positives.reduce((a, b) => a + b.value * b.weight, 0) / weightSum : 0;

  const flags = activeRiskFlags(c, p, cfg);
  const penalty = riskPenalty(flags, cfg);

  const total = clamp(positiveScore - penalty * w.risk, 0, 100);

  return {
    total,
    parts: {
      demand: demand ?? 0,
      profit,
      turnover: turnover ?? 0,
      competition: competition ?? 0,
      riskPenalty: penalty,
    },
    missing,
    activeFlags: flags,
  };
}

/**
 * Terapeak の実売平均と Browse API の出品中中央値の乖離。
 * 乖離が大きい＝想定売値の前提が崩れている可能性を警告する。
 */
export function priceDivergence(c: Candidate): { rate: number; note: string } | null {
  const sold = c.demand?.avgSoldPriceUsd;
  const active = c.market?.medianUsd;
  if (!sold || !active || sold <= 0) return null;
  const rate = (active - sold) / sold;
  const pct = Math.round(rate * 100);
  if (rate > 0.25) {
    return { rate, note: `出品中の中央値が実売平均より ${pct}% 高い（売れ残り相場の可能性）` };
  }
  if (rate < -0.25) {
    return { rate, note: `出品中の中央値が実売平均より ${Math.abs(pct)}% 低い（値崩れの可能性）` };
  }
  return { rate, note: `実売平均と出品中相場の乖離 ${pct}%（許容範囲）` };
}
