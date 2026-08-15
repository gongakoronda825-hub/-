import { describe, expect, it } from 'vitest';
import { defaultSettings, DESTINATIONS } from '../defaults';
import { evaluate } from '../evaluate';
import { resolveShipping } from '../profit';
import { validateBackup } from '../../storage/backup';
import type { Candidate } from '../types';

/**
 * config/*.json が壊れていないことを固定する。
 * 料率や送料の「値」は運用で変わるので検証しない。構造と整合性だけを見る。
 */
describe('config の雛形', () => {
  const s = defaultSettings();

  it('料率が数値として揃っている', () => {
    expect(s.rates.fx_jpy_per_usd).toBeGreaterThan(0);
    expect(s.rates.ebay.final_value_rate).toBeGreaterThan(0);
    expect(s.rates.ebay.international_fee_rate).toBeGreaterThanOrEqual(0);
    expect(s.rates.payout_fee_rate).toBeGreaterThanOrEqual(0);
    expect(s.rates.misc_jpy_per_item).toBeGreaterThanOrEqual(0);
  });

  it('手数料率の合計が100%未満（そうでないと売値を上げても利益が出ない）', () => {
    const sum =
      s.rates.ebay.final_value_rate +
      s.rates.ebay.international_fee_rate +
      s.rates.ebay.promoted_rate +
      s.rates.payout_fee_rate;
    expect(sum).toBeLessThan(1);
  });

  it('送料表の重量帯が昇順で、円が正の数', () => {
    for (const [key, method] of Object.entries(s.shipping.methods)) {
      for (const [zone, bands] of Object.entries(method.zones)) {
        expect(bands.length, `${key}/${zone} が空`).toBeGreaterThan(0);
        let prev = 0;
        for (const b of bands) {
          expect(b.max_g, `${key}/${zone} の重量帯が昇順でない`).toBeGreaterThan(prev);
          expect(b.jpy, `${key}/${zone} の料金が不正`).toBeGreaterThan(0);
          prev = b.max_g;
        }
      }
    }
  });

  it('既定の発送方法が既定の仕向地をカバーしている', () => {
    const r = resolveShipping(s.shipping, s.defaultShipMethod, s.defaultDestination, 300);
    expect(r.found).toBe(true);
    expect(r.jpy).toBeGreaterThan(0);
  });

  it('選択できる仕向地がすべてゾーンに解決できる', () => {
    for (const d of DESTINATIONS) {
      const zone = s.shipping.zone_of_country[d.code] ?? s.shipping.default_zone;
      const method = s.shipping.methods[s.defaultShipMethod];
      expect(method.zones[zone], `${d.code} → ${zone} の料金が無い`).toBeDefined();
    }
  });

  it('スコアの重みが正で、リスク減点が全フラグ分ある', () => {
    for (const [k, v] of Object.entries(s.scoring.weights)) {
      expect(v, `重み ${k}`).toBeGreaterThan(0);
    }
    for (const flag of ['vero_brand', 'cites', 'low_ticket', 'thin_margin', 'category_restricted']) {
      expect(s.scoring.risk.penalties[flag], `減点 ${flag}`).toBeGreaterThan(0);
    }
  });

  it('リスク辞書のキーワードが空でない', () => {
    expect(s.risk.rules.length).toBeGreaterThan(0);
    for (const rule of s.risk.rules) {
      expect(rule.keywords.length, rule.flag).toBeGreaterThan(0);
    }
  });
});

describe('evaluate（雛形設定での通し計算）', () => {
  it('黒字候補が正の利益とスコアを返す', () => {
    const s = defaultSettings();
    const c: Candidate = {
      id: 'x',
      title: 'Pentax K1000 35mm Camera',
      category: 'Cameras & Photo',
      sellPriceUsd: 145,
      costJpy: 9000,
      weightG: 500,
      destination: 'US',
      shipMethod: 'epacket_light',
      promoted: false,
      demand: { soldCount: 26, sellThroughRate: 0.71, periodDays: 90, source: 'terapeak-csv' },
      riskFlags: [],
      watch: false,
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-01T00:00:00.000Z',
    };
    const { profit, score, suggestedRisks } = evaluate(c, s);
    expect(profit.profitJpy).toBeGreaterThan(0);
    expect(profit.shipping.found).toBe(true);
    expect(score.total).toBeGreaterThan(0);
    expect(score.total).toBeLessThanOrEqual(100);
    // 競合データが無いことは検出される
    expect(score.missing.join()).toContain('競合');
    // "camera" は電池同梱の注意対象としてサジェストされる
    expect(suggestedRisks).toContain('battery');
  });
});

describe('validateBackup', () => {
  it('他アプリのJSONを弾く', () => {
    expect(() => validateBackup({ app: 'something-else' })).toThrow();
    expect(() => validateBackup(null)).toThrow();
    expect(() => validateBackup({ app: 'ebay-profit', candidates: [] })).toThrow(/settings/);
  });

  it('正しいバックアップを受け入れ、snapshots が無ければ空配列で補う', () => {
    const b = validateBackup({
      app: 'ebay-profit',
      version: 1,
      settings: defaultSettings(),
      candidates: [],
    });
    expect(b.snapshots).toEqual([]);
  });
});
