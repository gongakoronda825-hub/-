import { decimalsFor, formatMinor, formatSignedMinor } from '../src/lib/currency';
import { splitEvenly, toMinor } from '../src/lib/money';
import { calculateBalances, calculateTransfers, settleTrip } from '../src/lib/settlement';
import { parseAmount, validatePayment, validateTrip } from '../src/lib/validation';
import type { CurrencyCode, Member, Payment, Trip } from '../src/types';

/** テスト用に名前だけでメンバーを組み立てる。id は名前そのものにして読みやすくする。 */
function members(...names: string[]): Member[] {
  return names.map((name) => ({ id: name, name }));
}

function payment(
  id: string,
  payerId: string,
  amount: number,
  participantIds: string[]
): Payment {
  return { id, payerId, amount, description: id, participantIds, createdAt: '2026-01-01T00:00:00.000Z' };
}

function trip(currency: CurrencyCode, names: string[], payments: Payment[]): Trip {
  return {
    id: 'trip',
    name: 'テスト旅行',
    currency,
    members: members(...names),
    payments,
    createdAt: '2026-01-01T00:00:00.000Z',
  };
}

/** 収支を { メンバー名: 最小単位の金額 } に変換する。 */
function balanceMap(t: Trip): Record<string, number> {
  const result: Record<string, number> = {};
  for (const b of settleTrip(t).balances) {
    result[b.memberId] = b.amountMinor;
  }
  return result;
}

describe('splitEvenly（端数処理）', () => {
  it('割り切れるときは全員同額', () => {
    expect(splitEvenly(12000, 4)).toEqual([3000, 3000, 3000, 3000]);
  });

  it('割り切れないときも合計は必ず元の金額と一致する', () => {
    for (const [total, count] of [
      [20000, 3],
      [1, 4],
      [100, 7],
      [999999, 6],
    ] as const) {
      const shares = splitEvenly(total, count);
      expect(shares).toHaveLength(count);
      expect(shares.reduce((a, b) => a + b, 0)).toBe(total);
      // 端数は1単位までしかズレない
      expect(Math.max(...shares) - Math.min(...shares)).toBeLessThanOrEqual(1);
    }
  });

  it('端数は先頭の人から1ずつ配る', () => {
    expect(splitEvenly(20000, 3)).toEqual([6667, 6667, 6666]);
  });

  it('対象者が0人なら例外を投げる', () => {
    expect(() => splitEvenly(1000, 0)).toThrow();
  });
});

// 仕様書 18. テスト
describe('テスト1: 4人で12,000円をAが支払う', () => {
  const t = trip('JPY', ['A', 'B', 'C', 'D'], [payment('p1', 'A', 12000, ['A', 'B', 'C', 'D'])]);

  it('支払った本人も負担者に含めて計算する', () => {
    expect(balanceMap(t)).toEqual({ A: 9000, B: -3000, C: -3000, D: -3000 });
  });

  it('収支の合計は0になる', () => {
    const total = Object.values(balanceMap(t)).reduce((a, b) => a + b, 0);
    expect(total).toBe(0);
  });
});

describe('テスト2: A 10,000 / B 10,000 / C 0 を3人で均等利用', () => {
  const payments = [
    payment('p1', 'A', 10000, ['A', 'B', 'C']),
    payment('p2', 'B', 10000, ['A', 'B', 'C']),
  ];

  it('小数のない通貨（JPY）でも合計は1円もズレない', () => {
    const balances = balanceMap(trip('JPY', ['A', 'B', 'C'], payments));
    expect(balances.A + balances.B + balances.C).toBe(0);
    // 1人あたり 6,666.67 円 -> 端数配分で 6,666 or 6,667 円ずつ負担する
    expect(balances.C).toBe(-6666);
    expect(balances.A).toBeGreaterThan(0);
    expect(balances.B).toBeGreaterThan(0);
  });

  it('小数のある通貨（USD）では1セント単位まで配分する', () => {
    // 1人あたり 20000 / 3 = 6666.666... -> 6666.67 / 6666.67 / 6666.66
    const shares = splitEvenly(toMinor(20000, 2), 3);
    expect(shares).toEqual([666667, 666667, 666666]);
    expect(shares.reduce((a, b) => a + b, 0)).toBe(toMinor(20000, 2));

    const balances = balanceMap(trip('USD', ['A', 'B', 'C'], payments));
    expect(balances.A + balances.B + balances.C).toBe(0);
    expect(balances.C).toBe(-666666);
  });
});

describe('テスト3: AとBだけで6,000円をAが支払う', () => {
  const t = trip('JPY', ['A', 'B', 'C', 'D'], [payment('p1', 'A', 6000, ['A', 'B'])]);

  it('対象外のCとDは0のまま', () => {
    expect(balanceMap(t)).toEqual({ A: 3000, B: -3000, C: 0, D: 0 });
  });
});

describe('テスト4: 複数の支払いをまとめた精算結果', () => {
  const t = trip(
    'JPY',
    ['あおい', 'A', 'B', 'C'],
    [
      payment('p1', 'あおい', 30000, ['あおい', 'A', 'B', 'C']),
      payment('p2', 'A', 20000, ['あおい', 'A', 'B', 'C']),
      payment('p3', 'B', 10000, ['あおい', 'A', 'B', 'C']),
    ]
  );

  it('各メンバーの収支が正しい', () => {
    expect(balanceMap(t)).toEqual({ あおい: 15000, A: 5000, B: -5000, C: -15000 });
  });

  it('最小回数の送金にまとまる', () => {
    expect(settleTrip(t).transfers).toEqual([
      { fromId: 'C', toId: 'あおい', amountMinor: 15000 },
      { fromId: 'B', toId: 'A', amountMinor: 5000 },
    ]);
  });

  it('送金回数は（関係者数 − 1）回以下', () => {
    const { balances, transfers } = settleTrip(t);
    const involved = balances.filter((b) => b.amountMinor !== 0).length;
    expect(transfers.length).toBeLessThanOrEqual(Math.max(involved - 1, 0));
  });
});

describe('テスト5: 支払いを編集すると精算結果が更新される', () => {
  const before = trip(
    'JPY',
    ['A', 'B', 'C', 'D'],
    [payment('p1', 'A', 12000, ['A', 'B', 'C', 'D'])]
  );

  it('金額を変えると収支が変わる', () => {
    const after: Trip = {
      ...before,
      payments: [payment('p1', 'A', 8000, ['A', 'B', 'C', 'D'])],
    };
    expect(balanceMap(before)).toEqual({ A: 9000, B: -3000, C: -3000, D: -3000 });
    expect(balanceMap(after)).toEqual({ A: 6000, B: -2000, C: -2000, D: -2000 });
  });

  it('支払い対象者を変えると収支が変わる', () => {
    const after: Trip = { ...before, payments: [payment('p1', 'A', 12000, ['A', 'B'])] };
    expect(balanceMap(after)).toEqual({ A: 6000, B: -6000, C: 0, D: 0 });
  });

  it('支払った人を変えると収支が変わる', () => {
    const after: Trip = {
      ...before,
      payments: [payment('p1', 'B', 12000, ['A', 'B', 'C', 'D'])],
    };
    expect(balanceMap(after)).toEqual({ A: -3000, B: 9000, C: -3000, D: -3000 });
  });
});

describe('テスト6: 支払いを削除すると精算結果が更新される', () => {
  const t = trip(
    'JPY',
    ['A', 'B', 'C'],
    [payment('p1', 'A', 3000, ['A', 'B', 'C']), payment('p2', 'B', 6000, ['A', 'B', 'C'])]
  );

  it('削除後の収支に、消した支払いが影響しない', () => {
    const after: Trip = { ...t, payments: t.payments.filter((p) => p.id !== 'p2') };
    expect(balanceMap(t)).toEqual({ A: 0, B: 3000, C: -3000 });
    expect(balanceMap(after)).toEqual({ A: 2000, B: -1000, C: -1000 });
  });

  it('すべて削除すると全員0・送金なしになる', () => {
    const empty: Trip = { ...t, payments: [] };
    const { balances, transfers } = settleTrip(empty);
    expect(balances.every((b) => b.amountMinor === 0)).toBe(true);
    expect(transfers).toEqual([]);
  });
});

describe('calculateTransfers（仕様書 8. 精算アルゴリズム）', () => {
  it('仕様書の例どおりに送金をまとめる', () => {
    expect(
      calculateTransfers([
        { memberId: 'A', amountMinor: 10000 },
        { memberId: 'B', amountMinor: -6000 },
        { memberId: 'C', amountMinor: -4000 },
      ])
    ).toEqual([
      { fromId: 'B', toId: 'A', amountMinor: 6000 },
      { fromId: 'C', toId: 'A', amountMinor: 4000 },
    ]);
  });

  it('送金額の合計は受け取り側の合計と一致する', () => {
    const balances = [
      { memberId: 'A', amountMinor: 7000 },
      { memberId: 'B', amountMinor: 2500 },
      { memberId: 'C', amountMinor: -4500 },
      { memberId: 'D', amountMinor: -5000 },
    ];
    const transfers = calculateTransfers(balances);
    const sent = transfers.reduce((sum, t) => sum + t.amountMinor, 0);
    expect(sent).toBe(9500);
    expect(transfers.length).toBeLessThanOrEqual(balances.length - 1);
  });

  it('全員0なら送金は発生しない', () => {
    expect(calculateTransfers([{ memberId: 'A', amountMinor: 0 }])).toEqual([]);
  });
});

describe('calculateBalances の防御的な挙動', () => {
  it('存在しないメンバーを参照する支払いは無視する', () => {
    const ms = members('A', 'B');
    const payments = [payment('p1', 'X', 1000, ['X', 'Y'])];
    expect(calculateBalances(ms, payments, 0)).toEqual([
      { memberId: 'A', amountMinor: 0 },
      { memberId: 'B', amountMinor: 0 },
    ]);
  });

  it('支払った人が対象者に含まれない場合、全額が立て替えになる', () => {
    const ms = members('A', 'B', 'C');
    const payments = [payment('p1', 'A', 6000, ['B', 'C'])];
    expect(calculateBalances(ms, payments, 0)).toEqual([
      { memberId: 'A', amountMinor: 6000 },
      { memberId: 'B', amountMinor: -3000 },
      { memberId: 'C', amountMinor: -3000 },
    ]);
  });
});

describe('通貨の表示', () => {
  it('通貨ごとの最小単位', () => {
    expect(decimalsFor('JPY')).toBe(0);
    expect(decimalsFor('KRW')).toBe(0);
    expect(decimalsFor('USD')).toBe(2);
  });

  it('円は「◯◯円」、それ以外は通貨コードを後ろに付ける', () => {
    expect(formatMinor(18750, 'JPY')).toBe('18,750円');
    expect(formatMinor(30000, 'KRW')).toBe('30,000 KRW');
    expect(formatMinor(123456, 'USD')).toBe('1,234.56 USD');
  });

  it('収支は符号付きで表示する', () => {
    expect(formatSignedMinor(18750, 'JPY')).toBe('+18,750円');
    expect(formatSignedMinor(-1250, 'JPY')).toBe('−1,250円');
    expect(formatSignedMinor(0, 'JPY')).toBe('±0円');
  });
});

describe('入力チェック（仕様書 16. エラー処理）', () => {
  it('旅行名が空ならエラー', () => {
    expect(validateTrip({ name: '  ', memberNames: ['A', 'B'] })).toBe('旅行名を入力してください');
  });

  it('メンバーが2人未満ならエラー', () => {
    expect(validateTrip({ name: '韓国旅行', memberNames: ['A', ''] })).toBe(
      'メンバーを2人以上入力してください'
    );
  });

  it('同名メンバーはエラー', () => {
    expect(validateTrip({ name: '韓国旅行', memberNames: ['A', 'A'] })).toBe(
      '同じ名前のメンバーがいます。区別できる名前にしてください'
    );
  });

  it('正しい入力ならエラーなし', () => {
    expect(validateTrip({ name: '韓国旅行2026', memberNames: ['あおい', 'A'] })).toBeNull();
  });

  it('支払った人が未選択ならエラー', () => {
    expect(validatePayment({ payerId: null, amountText: '1000', participantIds: ['A'] })).toBe(
      '支払った人を選択してください'
    );
  });

  it('金額が数字でなければエラー', () => {
    expect(validatePayment({ payerId: 'A', amountText: 'abc', participantIds: ['A'] })).toBe(
      '金額は数字で入力してください'
    );
    expect(validatePayment({ payerId: 'A', amountText: '', participantIds: ['A'] })).toBe(
      '金額は数字で入力してください'
    );
  });

  it('金額が0以下ならエラー', () => {
    expect(validatePayment({ payerId: 'A', amountText: '0', participantIds: ['A'] })).toBe(
      '金額は0より大きい数字を入力してください'
    );
  });

  it('支払い対象者が0人ならエラー', () => {
    expect(validatePayment({ payerId: 'A', amountText: '1000', participantIds: [] })).toBe(
      '支払い対象者を1人以上選んでください'
    );
  });

  it('正しい入力ならエラーなし', () => {
    expect(
      validatePayment({ payerId: 'A', amountText: '12,000', participantIds: ['A', 'B'] })
    ).toBeNull();
  });
});

describe('parseAmount', () => {
  it('カンマ区切りと全角数字を受け付ける', () => {
    expect(parseAmount('12,000')).toBe(12000);
    expect(parseAmount('１２３')).toBe(123);
    expect(parseAmount('12.50')).toBe(12.5);
  });

  it('数字として読めない入力は null', () => {
    expect(parseAmount('')).toBeNull();
    expect(parseAmount('abc')).toBeNull();
    expect(parseAmount('1-2')).toBeNull();
    expect(parseAmount('.')).toBeNull();
  });
});
