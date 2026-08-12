import type { CurrencyCode, Member, Payment, Trip } from '../types';
import { decimalsFor } from './currency';
import { splitEvenly, toMinor } from './money';

/**
 * 精算計算。UI から完全に独立した純粋関数だけで構成する。
 * 金額はすべて最小単位（円・セント）の整数で扱う。
 */

export type Balance = {
  memberId: string;
  /** 実際に支払った額 − 本来負担すべき額。プラスなら受け取る側。 */
  amountMinor: number;
};

export type Transfer = {
  fromId: string;
  toId: string;
  amountMinor: number;
};

export type Settlement = {
  currency: CurrencyCode;
  balances: Balance[];
  transfers: Transfer[];
};

/**
 * 各メンバーの収支を計算する。
 *
 * 1件の支払いにつき
 *   - 支払った人に「支払った全額」を加算
 *   - 支払い対象者それぞれに「1人あたりの負担額」を減算
 * する。支払った人が対象者に含まれていれば、その人も負担者として引かれる。
 *
 * 端数は splitEvenly が配分するので、戻り値の合計は必ず 0 になる。
 */
export function calculateBalances(
  members: Member[],
  payments: Payment[],
  decimals: number
): Balance[] {
  const totals = new Map<string, number>(members.map((m) => [m.id, 0]));
  const add = (memberId: string, delta: number) => {
    // 既に削除されたメンバーを参照している支払いは無視する
    if (!totals.has(memberId)) return;
    totals.set(memberId, (totals.get(memberId) as number) + delta);
  };

  for (const payment of payments) {
    const participants = payment.participantIds.filter((id) => totals.has(id));
    if (participants.length === 0) continue;

    const amountMinor = toMinor(payment.amount, decimals);
    add(payment.payerId, amountMinor);

    const shares = splitEvenly(amountMinor, participants.length);
    participants.forEach((id, i) => add(id, -shares[i]));
  }

  return members.map((m) => ({ memberId: m.id, amountMinor: totals.get(m.id) ?? 0 }));
}

/**
 * 収支から「誰が誰にいくら払うか」を求める。
 *
 * 受け取る側・支払う側をそれぞれ金額の大きい順に並べ、
 * 大きいもの同士を突き合わせて消し込む貪欲法。
 * 送金回数は必ず (関係者数 − 1) 回以下に収まる。
 *
 * 入力の合計が 0 であること（calculateBalances の保証）を前提とする。
 */
export function calculateTransfers(balances: Balance[]): Transfer[] {
  // 元の並び順を同額時のタイブレークに使い、結果を常に一意にする
  const order = new Map(balances.map((b, i) => [b.memberId, i]));
  const byAmountDesc = (a: Balance, b: Balance) =>
    b.amountMinor - a.amountMinor ||
    (order.get(a.memberId) as number) - (order.get(b.memberId) as number);

  // 消し込みで残額を書き換えるので、必ず複製してから扱う（引数を壊さない）
  const creditors = balances
    .filter((b) => b.amountMinor > 0)
    .map((b) => ({ ...b }))
    .sort(byAmountDesc);
  const debtors = balances
    .filter((b) => b.amountMinor < 0)
    .map((b) => ({ ...b, amountMinor: -b.amountMinor }))
    .sort(byAmountDesc);

  const transfers: Transfer[] = [];
  let ci = 0;
  let di = 0;

  while (ci < creditors.length && di < debtors.length) {
    const creditor = creditors[ci];
    const debtor = debtors[di];
    const amountMinor = Math.min(creditor.amountMinor, debtor.amountMinor);

    if (amountMinor > 0) {
      transfers.push({ fromId: debtor.memberId, toId: creditor.memberId, amountMinor });
      creditor.amountMinor -= amountMinor;
      debtor.amountMinor -= amountMinor;
    }

    if (creditor.amountMinor === 0) ci += 1;
    if (debtor.amountMinor === 0) di += 1;
  }

  return transfers;
}

/** 旅行1件から収支と送金リストをまとめて求める。 */
export function settleTrip(trip: Trip): Settlement {
  const decimals = decimalsFor(trip.currency);
  const balances = calculateBalances(trip.members, trip.payments, decimals);
  return { currency: trip.currency, balances, transfers: calculateTransfers(balances) };
}
