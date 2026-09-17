import { describe, expect, it } from 'vitest';
import {
  guessMapping,
  parseCsvText,
  parseNumber,
  parseRate,
  rowsToCandidates,
} from '../../datasources/terapeakCsv';

const SAMPLE = `Product name,Avg sold price,Total sold,Sell-through,Category
"Nintendo Game Boy Pocket",$78.50,42,"83%","Video Games"
"Seiko SKX007 Diver",$310.00,12,"55%","Watches"
"",$10.00,3,"20%","Misc"
`;

describe('parseNumber / parseRate', () => {
  it('通貨記号とカンマを外す', () => {
    expect(parseNumber('$1,234.56')).toBeCloseTo(1234.56, 6);
    expect(parseNumber('¥1,200')).toBe(1200);
    expect(parseNumber('42')).toBe(42);
  });

  it('空や解釈不能は undefined', () => {
    expect(parseNumber('')).toBeUndefined();
    expect(parseNumber(null)).toBeUndefined();
    expect(parseNumber('N/A')).toBeUndefined();
    expect(parseNumber('-')).toBeUndefined();
  });

  it('%表記と小数の両方を 0-1 に正規化する', () => {
    expect(parseRate('83%')).toBeCloseTo(0.83, 6);
    expect(parseRate('0.83')).toBeCloseTo(0.83, 6);
    expect(parseRate('83')).toBeCloseTo(0.83, 6);
    expect(parseRate('')).toBeUndefined();
  });
});

describe('parseCsvText', () => {
  it('ヘッダと行を取り出し、空行を捨てる', () => {
    const { headers, rows } = parseCsvText(SAMPLE);
    expect(headers).toEqual(['Product name', 'Avg sold price', 'Total sold', 'Sell-through', 'Category']);
    expect(rows).toHaveLength(3);
    expect(rows[0]['Product name']).toBe('Nintendo Game Boy Pocket');
  });
});

describe('guessMapping', () => {
  it('Terapeak の標準的な列名を推測できる', () => {
    const { headers } = parseCsvText(SAMPLE);
    const m = guessMapping(headers);
    expect(m.title).toBe('Product name');
    expect(m.avgSoldPriceUsd).toBe('Avg sold price');
    expect(m.soldCount).toBe('Total sold');
    expect(m.sellThroughRate).toBe('Sell-through');
    expect(m.category).toBe('Category');
  });

  it('列名の揺れ（大文字・アンダースコア・日本語）を吸収する', () => {
    const m = guessMapping(['Item_Title', 'AVERAGE SOLD PRICE', 'Items Sold', '売却率']);
    expect(m.title).toBe('Item_Title');
    expect(m.avgSoldPriceUsd).toBe('AVERAGE SOLD PRICE');
    expect(m.soldCount).toBe('Items Sold');
    expect(m.sellThroughRate).toBe('売却率');
  });

  it('該当列が無ければ未設定のまま（UIで手動マッピングする前提）', () => {
    const m = guessMapping(['foo', 'bar']);
    expect(m.title).toBeUndefined();
  });
});

describe('rowsToCandidates', () => {
  const defaults = {
    costJpy: 0,
    weightG: 500,
    destination: 'US',
    shipMethod: 'epacket_light',
    promoted: false,
    periodDays: 90,
  };

  it('CSVから候補を一括生成し、需要指標を紐づける', () => {
    const { headers, rows } = parseCsvText(SAMPLE);
    const results = rowsToCandidates(rows, guessMapping(headers), defaults);

    const made = results.filter((r) => r.candidate).map((r) => r.candidate!);
    expect(made).toHaveLength(2);

    const gb = made[0];
    expect(gb.title).toBe('Nintendo Game Boy Pocket');
    // 平均売値が想定売値USDの初期値になる
    expect(gb.sellPriceUsd).toBeCloseTo(78.5, 6);
    expect(gb.demand?.soldCount).toBe(42);
    expect(gb.demand?.sellThroughRate).toBeCloseTo(0.83, 6);
    expect(gb.demand?.periodDays).toBe(90);
    expect(gb.demand?.source).toBe('terapeak-csv');
    expect(gb.category).toBe('Video Games');
    expect(gb.weightG).toBe(500);
  });

  it('商品名が空の行はスキップ理由付きで返す', () => {
    const { headers, rows } = parseCsvText(SAMPLE);
    const results = rowsToCandidates(rows, guessMapping(headers), defaults);
    const skipped = results.filter((r) => r.skipped);
    expect(skipped).toHaveLength(1);
    expect(skipped[0].skipped).toContain('商品名');
  });

  it('売値の列が無い場合は0で作り、手入力に回す', () => {
    const { headers, rows } = parseCsvText(SAMPLE);
    const mapping = { ...guessMapping(headers), avgSoldPriceUsd: undefined };
    const results = rowsToCandidates(rows, mapping, defaults);
    expect(results[0].candidate?.sellPriceUsd).toBe(0);
  });

  it('生成される候補のIDは重複しない', () => {
    const { headers, rows } = parseCsvText(SAMPLE);
    const results = rowsToCandidates(rows, guessMapping(headers), defaults);
    const ids = results.filter((r) => r.candidate).map((r) => r.candidate!.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
