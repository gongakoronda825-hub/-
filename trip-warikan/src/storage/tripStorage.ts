import AsyncStorage from '@react-native-async-storage/async-storage';

import { CURRENCIES } from '../lib/currency';
import type { CurrencyCode, Member, Payment, Trip } from '../types';

const STORAGE_KEY = 'trip-warikan/trips/v1';

const CURRENCY_CODES = new Set<string>(CURRENCIES.map((c) => c.code));

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

/**
 * 保存済み JSON は端末に長く残るので、読み込み時に必ず形を検証する。
 * 壊れた項目は捨てて、読める分だけ復元する（起動できなくなるのを防ぐ）。
 */
function parseMember(value: unknown): Member | null {
  if (!isRecord(value)) return null;
  const { id, name } = value;
  if (typeof id !== 'string' || typeof name !== 'string') return null;
  return { id, name };
}

function parsePayment(value: unknown, memberIds: Set<string>): Payment | null {
  if (!isRecord(value)) return null;
  const { id, payerId, amount, description, participantIds, createdAt } = value;
  if (typeof id !== 'string' || typeof payerId !== 'string') return null;
  if (typeof amount !== 'number' || !Number.isFinite(amount)) return null;
  if (!Array.isArray(participantIds)) return null;
  const participants = participantIds.filter(
    (pid): pid is string => typeof pid === 'string' && memberIds.has(pid)
  );
  if (!memberIds.has(payerId) || participants.length === 0) return null;
  return {
    id,
    payerId,
    amount,
    description: typeof description === 'string' ? description : '',
    participantIds: participants,
    createdAt: typeof createdAt === 'string' ? createdAt : new Date().toISOString(),
  };
}

function parseTrip(value: unknown): Trip | null {
  if (!isRecord(value)) return null;
  const { id, name, currency, members, payments, createdAt } = value;
  if (typeof id !== 'string' || typeof name !== 'string') return null;
  if (typeof currency !== 'string' || !CURRENCY_CODES.has(currency)) return null;
  if (!Array.isArray(members)) return null;

  const parsedMembers = members
    .map(parseMember)
    .filter((m): m is Member => m !== null);
  if (parsedMembers.length === 0) return null;

  const memberIds = new Set(parsedMembers.map((m) => m.id));
  const parsedPayments = Array.isArray(payments)
    ? payments
        .map((p) => parsePayment(p, memberIds))
        .filter((p): p is Payment => p !== null)
    : [];

  return {
    id,
    name,
    currency: currency as CurrencyCode,
    members: parsedMembers,
    payments: parsedPayments,
    createdAt: typeof createdAt === 'string' ? createdAt : new Date().toISOString(),
  };
}

export async function loadTrips(): Promise<Trip[]> {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(parseTrip).filter((t): t is Trip => t !== null);
  } catch {
    // JSON が壊れている場合でもアプリは起動させる
    return [];
  }
}

export async function saveTrips(trips: Trip[]): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
}
