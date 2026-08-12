/**
 * 入力チェック。エラー文言はすべて日本語で、何をすれば直るかが分かる書き方にする。
 * 戻り値が null ならエラーなし。
 */

export type TripDraft = {
  name: string;
  memberNames: string[];
};

export type PaymentDraft = {
  payerId: string | null;
  /** 入力欄の生の文字列。数値変換もここで検証する。 */
  amountText: string;
  participantIds: string[];
};

export function validateTrip(draft: TripDraft): string | null {
  if (draft.name.trim() === '') {
    return '旅行名を入力してください';
  }
  const names = draft.memberNames.map((n) => n.trim()).filter((n) => n !== '');
  if (names.length < 2) {
    return 'メンバーを2人以上入力してください';
  }
  if (new Set(names).size !== names.length) {
    return '同じ名前のメンバーがいます。区別できる名前にしてください';
  }
  return null;
}

/**
 * 金額文字列を数値に変換する。数字として解釈できなければ null。
 * 全角数字・カンマ区切りの入力も受け付ける。
 */
export function parseAmount(text: string): number | null {
  const normalized = text
    .trim()
    .replace(/[０-９．]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xfee0))
    .replace(/,/g, '');
  if (normalized === '' || !/^\d*\.?\d*$/.test(normalized) || normalized === '.') {
    return null;
  }
  const value = Number(normalized);
  return Number.isFinite(value) ? value : null;
}

export function validatePayment(draft: PaymentDraft): string | null {
  if (!draft.payerId) {
    return '支払った人を選択してください';
  }
  const amount = parseAmount(draft.amountText);
  if (amount === null) {
    return '金額は数字で入力してください';
  }
  if (amount <= 0) {
    return '金額は0より大きい数字を入力してください';
  }
  if (draft.participantIds.length === 0) {
    return '支払い対象者を1人以上選んでください';
  }
  return null;
}
