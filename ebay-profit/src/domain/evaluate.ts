import { computeProfit } from './profit';
import { computeScore } from './score';
import { suggestRiskFlags } from './risk';
import type {
  AppSettings,
  Candidate,
  ManualRiskFlag,
  ProfitBreakdown,
  ScoreResult,
} from './types';

export interface Evaluated {
  candidate: Candidate;
  profit: ProfitBreakdown;
  score: ScoreResult;
  /** キーワードから提案されたが、まだ手動チェックで確定していないリスク */
  suggestedRisks: ManualRiskFlag[];
}

/** 候補 × 現在の設定 → 着地利益とスコア。画面はすべてこれを通す。 */
export function evaluate(c: Candidate, settings: AppSettings): Evaluated {
  const profit = computeProfit(
    {
      sellPriceUsd: c.sellPriceUsd,
      costJpy: c.costJpy,
      weightG: c.weightG,
      destination: c.destination,
      shipMethod: c.shipMethod,
      shippingOverrideJpy: c.shippingOverrideJpy,
      promoted: c.promoted,
      category: c.category,
    },
    settings.rates,
    settings.shipping,
  );
  const score = computeScore(c, profit, settings.scoring);
  const suggestedRisks = suggestRiskFlags(`${c.title} ${c.category ?? ''}`, settings.risk)
    .map((s) => s.flag)
    .filter((f) => !c.riskFlags.includes(f));
  return { candidate: c, profit, score, suggestedRisks };
}

export function evaluateAll(list: Candidate[], settings: AppSettings): Evaluated[] {
  return list.map((c) => evaluate(c, settings));
}
