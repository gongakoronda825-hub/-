import type { ManualRiskFlag, RiskConfig, RiskFlag } from './types';

export const RISK_LABELS: Record<RiskFlag, string> = {
  vero_brand: 'VeRO/ブランド規制',
  cites: 'ワシントン条約(CITES)',
  food_cosmetics: '食品・化粧品・医薬部外品',
  electronics_regulated: '電気製品（PSE/技適/電波法）',
  battery: 'リチウム電池',
  counterfeit_suspect: '模造品・海賊版の疑い',
  category_restricted: 'eBayカテゴリ出品制限',
  low_ticket: '低単価',
  thin_margin: '薄利',
};

/**
 * タイトル/カテゴリのキーワードからリスクフラグを「サジェスト」する。
 * あくまで足切りの当たりを付けるためのもので、確定は人が手動チェックで行う。
 */
export function suggestRiskFlags(
  text: string,
  config: RiskConfig,
): { flag: ManualRiskFlag; matched: string[] }[] {
  const haystack = (text || '').toLowerCase();
  if (!haystack) return [];

  const out: { flag: ManualRiskFlag; matched: string[] }[] = [];
  for (const rule of config.rules) {
    const matched = rule.keywords.filter((k) => k && haystack.includes(k.toLowerCase()));
    if (matched.length > 0) out.push({ flag: rule.flag, matched });
  }
  return out;
}

/** 送料方法とリスクフラグの整合チェック（例：電池はEMS不可のことがある） */
export function shippingWarnings(flags: RiskFlag[], shipMethod: string): string[] {
  const warnings: string[] = [];
  if (flags.includes('battery') && shipMethod !== 'fedex') {
    warnings.push('リチウム電池内蔵/同梱の疑い。郵便（EMS/eパケット）は内容品制限があるため、発送方法と申告内容を確認すること。');
  }
  if (flags.includes('food_cosmetics')) {
    warnings.push('食品・化粧品は仕向地の輸入規制（米国FDA等）と成分規制の確認が必要。');
  }
  if (flags.includes('cites')) {
    warnings.push('CITES該当品は輸出許可なしでは発送不可。該当が確定した時点で候補から外すこと。');
  }
  return warnings;
}
