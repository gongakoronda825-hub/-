import ratesJson from '../../config/rates.json';
import shippingJson from '../../config/shipping.json';
import scoringJson from '../../config/scoring.json';
import riskJson from '../../config/risk.json';
import type { AppSettings, Rates, RiskConfig, ScoringConfig, ShippingTable } from './types';

/**
 * config/*.json は「初期値の雛形」。実際に使う値は保存層（IndexedDB）にコピーされ、
 * 以後は設定画面から編集する。コードに料率を直書きしないための単一の入口。
 */
export const defaultRates = ratesJson as unknown as Rates;
export const defaultShipping = shippingJson as unknown as ShippingTable;
export const defaultScoring = scoringJson as unknown as ScoringConfig;
export const defaultRisk = riskJson as unknown as RiskConfig;

export function defaultSettings(): AppSettings {
  return {
    rates: structuredClone(defaultRates),
    shipping: structuredClone(defaultShipping),
    scoring: structuredClone(defaultScoring),
    risk: structuredClone(defaultRisk),
    apiBase: '/api',
    defaultDestination: 'US',
    defaultShipMethod: 'epacket_light',
  };
}

export const DESTINATIONS: { code: string; label: string }[] = [
  { code: 'US', label: 'アメリカ' },
  { code: 'CA', label: 'カナダ' },
  { code: 'GB', label: 'イギリス' },
  { code: 'DE', label: 'ドイツ' },
  { code: 'FR', label: 'フランス' },
  { code: 'AU', label: 'オーストラリア' },
  { code: 'HK', label: '香港' },
  { code: 'TW', label: '台湾' },
  { code: 'SG', label: 'シンガポール' },
  { code: 'KR', label: '韓国' },
];
