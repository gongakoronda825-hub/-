/**
 * アプリ全体で共有するドメイン型。
 * 保存形式（ローカルストレージの JSON）もこの型がそのまま使われる。
 */

export type CurrencyCode = 'JPY' | 'USD' | 'KRW' | 'TWD' | 'EUR' | 'GBP' | 'VND';

export type Member = {
  id: string;
  name: string;
};

export type Payment = {
  id: string;
  /** 立て替えた人の Member.id */
  payerId: string;
  /** 主単位の金額（例: 12000 円、12.5 ドル） */
  amount: number;
  /** 内容（例: タクシー、レストラン） */
  description: string;
  /** 割り勘の対象になる Member.id の一覧 */
  participantIds: string[];
  /** ISO 8601 文字列 */
  createdAt: string;
};

export type Trip = {
  id: string;
  name: string;
  currency: CurrencyCode;
  members: Member[];
  payments: Payment[];
  createdAt: string;
};
