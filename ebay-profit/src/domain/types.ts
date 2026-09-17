/** ドメイン型定義。数値は特記なき限り、金額は円 or USD、重量は g。 */

export type RiskFlag =
  | 'vero_brand'
  | 'cites'
  | 'food_cosmetics'
  | 'electronics_regulated'
  | 'battery'
  | 'counterfeit_suspect'
  | 'category_restricted'
  | 'low_ticket'
  | 'thin_margin';

/** 自動サジェスト対象のフラグ（low_ticket / thin_margin は計算から自動で立つ） */
export type ManualRiskFlag = Exclude<RiskFlag, 'low_ticket' | 'thin_margin'>;

export interface EbayRates {
  final_value_rate: number;
  category_final_value_rates?: Record<string, number>;
  international_fee_rate: number;
  promoted_rate: number;
  per_order_fixed_usd: number;
}

export interface Rates {
  fx_jpy_per_usd: number;
  fx_updated_at?: string | null;
  fx_manual_override?: boolean;
  ebay: EbayRates;
  payout_fee_rate: number;
  misc_jpy_per_item: number;
}

export interface ShippingBand {
  max_g: number;
  jpy: number;
}

export interface ShippingMethod {
  label: string;
  max_g?: number;
  zones: Record<string, ShippingBand[]>;
}

export interface ShippingTable {
  zone_of_country: Record<string, string>;
  default_zone: string;
  methods: Record<string, ShippingMethod>;
}

export interface ScoringConfig {
  weights: {
    demand: number;
    profit: number;
    turnover: number;
    competition: number;
    risk: number;
  };
  demand: { sold_count_full: number; sell_through_full: number };
  profit: { roi_full: number; profit_jpy_full: number; roi_share: number };
  turnover: { sold_per_month_full: number };
  competition: { active_listings_full: number };
  risk: {
    penalties: Record<string, number>;
    low_ticket_usd: number;
    thin_margin_rate: number;
  };
  alerts: {
    profit_drop_rate: number;
    min_profit_jpy: number;
    min_roi: number;
  };
}

export interface RiskRule {
  flag: ManualRiskFlag;
  label: string;
  hint: string;
  keywords: string[];
}

export interface RiskConfig {
  rules: RiskRule[];
}

/** Terapeak CSV 由来（または手動レンジ入力）の需要指標 */
export interface DemandData {
  avgSoldPriceUsd?: number;
  soldCount?: number;
  /** 0-1 */
  sellThroughRate?: number;
  /** 集計期間（日）。回転スコアの分母。 */
  periodDays?: number;
  source: 'terapeak-csv' | 'manual';
  fetchedAt?: string;
}

/** Browse API 由来の「出品中」相場 */
export interface MarketData {
  activeCount?: number;
  medianUsd?: number;
  p25Usd?: number;
  p75Usd?: number;
  fetchedAt?: string;
  query?: string;
}

export interface SupplierRef {
  name: string;
  url?: string;
  priceJpy?: number;
  source: 'manual' | 'rakuten' | 'yahoo';
}

export interface Candidate {
  id: string;
  title: string;
  category?: string;
  keyword?: string;
  notes?: string;

  /** 想定売値 */
  sellPriceUsd: number;
  /** 日本仕入れ値（税込） */
  costJpy: number;
  weightG: number;
  /** 仕向地の国コード（US など） */
  destination: string;
  shipMethod: string;
  /** 送料を手動で固定したい場合 */
  shippingOverrideJpy?: number | null;
  promoted: boolean;

  demand?: DemandData;
  market?: MarketData;
  suppliers?: SupplierRef[];

  riskFlags: ManualRiskFlag[];
  /** 自動サジェストされたが未確認のフラグ */
  riskSuggested?: ManualRiskFlag[];
  categoryRestricted?: boolean;

  watch: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ProfitInput {
  sellPriceUsd: number;
  costJpy: number;
  weightG: number;
  destination: string;
  shipMethod: string;
  shippingOverrideJpy?: number | null;
  promoted: boolean;
  category?: string;
}

export interface ShippingResolution {
  found: boolean;
  jpy: number;
  method: string;
  zone: string;
  bandMaxG?: number;
  reason?: string;
}

export interface ProfitBreakdown {
  fx: number;
  revenueJpy: number;
  /** eBay手数料の内訳 */
  finalValueJpy: number;
  internationalFeeJpy: number;
  promotedJpy: number;
  perOrderFixedJpy: number;
  ebayFeeJpy: number;
  payoutFeeJpy: number;
  costJpy: number;
  shippingJpy: number;
  miscJpy: number;
  profitJpy: number;
  /** 着地利益 ÷ 原価 */
  roi: number;
  /** 着地利益 ÷ 売上 */
  marginRate: number;
  shipping: ShippingResolution;
  finalValueRate: number;
}

export interface ScoreParts {
  demand: number;
  profit: number;
  turnover: number;
  competition: number;
  riskPenalty: number;
}

export interface ScoreResult {
  total: number;
  parts: ScoreParts;
  /** 計算に使えたデータが欠けている項目 */
  missing: string[];
  activeFlags: RiskFlag[];
}

/** ウォッチリストの再計算スナップショット */
export interface Snapshot {
  id?: number;
  candidateId: string;
  at: string;
  fx: number;
  sellPriceUsd: number;
  costJpy: number;
  profitJpy: number;
  roi: number;
  score: number;
  marketMedianUsd?: number;
  activeCount?: number;
}

export interface AppSettings {
  rates: Rates;
  shipping: ShippingTable;
  scoring: ScoringConfig;
  risk: RiskConfig;
  /** サーバーレスプロキシのベースURL。既定は同一オリジンの /api */
  apiBase: string;
  /** 既定の仕向地・発送方法 */
  defaultDestination: string;
  defaultShipMethod: string;
}
