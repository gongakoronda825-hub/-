import Dexie, { type Table } from 'dexie';
import type { AppSettings, Candidate, Snapshot } from '../domain/types';
import { defaultSettings } from '../domain/defaults';

/**
 * 保存層。(A) 端末内保存（IndexedDB）の実装。
 * 将来 (B) ホスト型DB同期に差し替えられるよう、UI からはこのモジュールの
 * 関数だけを呼ぶこと（Dexie のインスタンスを直接触らない）。
 */
class AppDb extends Dexie {
  candidates!: Table<Candidate, string>;
  snapshots!: Table<Snapshot, number>;
  settings!: Table<{ key: string; value: unknown }, string>;

  constructor() {
    super('ebay-profit');
    this.version(1).stores({
      candidates: 'id, title, watch, updatedAt',
      snapshots: '++id, candidateId, at',
      settings: 'key',
    });
  }
}

export const db = new AppDb();

const SETTINGS_KEY = 'app';

/** 保存済み設定を読む。無ければ config/*.json の雛形で初期化して保存する。 */
export async function loadSettings(): Promise<AppSettings> {
  const row = await db.settings.get(SETTINGS_KEY);
  if (!row) {
    const s = defaultSettings();
    await db.settings.put({ key: SETTINGS_KEY, value: s });
    return s;
  }
  // 雛形に後から増えたキーを埋める（古い保存データとの互換）
  return mergeSettings(defaultSettings(), row.value as Partial<AppSettings>);
}

export function mergeSettings(base: AppSettings, saved: Partial<AppSettings>): AppSettings {
  return {
    ...base,
    ...saved,
    rates: { ...base.rates, ...(saved.rates ?? {}), ebay: { ...base.rates.ebay, ...(saved.rates?.ebay ?? {}) } },
    shipping: { ...base.shipping, ...(saved.shipping ?? {}) },
    scoring: {
      ...base.scoring,
      ...(saved.scoring ?? {}),
      weights: { ...base.scoring.weights, ...(saved.scoring?.weights ?? {}) },
      risk: { ...base.scoring.risk, ...(saved.scoring?.risk ?? {}) },
      alerts: { ...base.scoring.alerts, ...(saved.scoring?.alerts ?? {}) },
    },
    risk: saved.risk ?? base.risk,
  };
}

export async function saveSettings(s: AppSettings): Promise<void> {
  await db.settings.put({ key: SETTINGS_KEY, value: s });
}

export async function resetSettings(): Promise<AppSettings> {
  const s = defaultSettings();
  await db.settings.put({ key: SETTINGS_KEY, value: s });
  return s;
}

export async function listCandidates(): Promise<Candidate[]> {
  return db.candidates.toArray();
}

export async function getCandidate(id: string): Promise<Candidate | undefined> {
  return db.candidates.get(id);
}

export async function putCandidate(c: Candidate): Promise<void> {
  await db.candidates.put({ ...c, updatedAt: new Date().toISOString() });
}

export async function putCandidates(list: Candidate[]): Promise<void> {
  await db.candidates.bulkPut(list);
}

export async function deleteCandidate(id: string): Promise<void> {
  await db.transaction('rw', db.candidates, db.snapshots, async () => {
    await db.candidates.delete(id);
    await db.snapshots.where('candidateId').equals(id).delete();
  });
}

export async function addSnapshot(s: Snapshot): Promise<void> {
  await db.snapshots.add(s);
}

export async function listSnapshots(candidateId: string): Promise<Snapshot[]> {
  const rows = await db.snapshots.where('candidateId').equals(candidateId).toArray();
  return rows.sort((a, b) => a.at.localeCompare(b.at));
}

export async function listAllSnapshots(): Promise<Snapshot[]> {
  return db.snapshots.toArray();
}

export async function clearAll(): Promise<void> {
  await db.transaction('rw', db.candidates, db.snapshots, db.settings, async () => {
    await db.candidates.clear();
    await db.snapshots.clear();
    await db.settings.clear();
  });
}
