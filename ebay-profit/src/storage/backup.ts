import type { AppSettings, Candidate, Snapshot } from '../domain/types';
import {
  clearAll,
  listAllSnapshots,
  listCandidates,
  loadSettings,
  putCandidates,
  saveSettings,
  db,
} from './db';

/**
 * JSON バックアップ。iOS Safari は「ホーム画面に追加」していない状態だと
 * IndexedDB が7日程度で消える場合があるため、これが唯一の保険になる。
 */

export const BACKUP_VERSION = 1;

export interface BackupFile {
  app: 'ebay-profit';
  version: number;
  exportedAt: string;
  settings: AppSettings;
  candidates: Candidate[];
  snapshots: Snapshot[];
}

export async function buildBackup(): Promise<BackupFile> {
  const [settings, candidates, snapshots] = await Promise.all([
    loadSettings(),
    listCandidates(),
    listAllSnapshots(),
  ]);
  return {
    app: 'ebay-profit',
    version: BACKUP_VERSION,
    exportedAt: new Date().toISOString(),
    settings,
    candidates,
    snapshots,
  };
}

export function validateBackup(data: unknown): BackupFile {
  if (!data || typeof data !== 'object') throw new Error('JSONの形式が不正です');
  const b = data as Partial<BackupFile>;
  if (b.app !== 'ebay-profit') throw new Error('このアプリのバックアップファイルではありません');
  if (!Array.isArray(b.candidates)) throw new Error('candidates が配列ではありません');
  if (!b.settings) throw new Error('settings がありません');
  return {
    app: 'ebay-profit',
    version: b.version ?? BACKUP_VERSION,
    exportedAt: b.exportedAt ?? new Date().toISOString(),
    settings: b.settings,
    candidates: b.candidates,
    snapshots: Array.isArray(b.snapshots) ? b.snapshots : [],
  };
}

export type RestoreMode = 'merge' | 'replace';

export async function restoreBackup(backup: BackupFile, mode: RestoreMode): Promise<void> {
  if (mode === 'replace') await clearAll();
  await saveSettings(backup.settings);
  await putCandidates(backup.candidates);
  if (backup.snapshots.length > 0) {
    // id は振り直す（merge時の衝突回避）
    await db.snapshots.bulkAdd(backup.snapshots.map(({ id: _id, ...rest }) => rest as Snapshot));
  }
}

export function downloadJson(filename: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function backupFilename(now = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `ebay-profit-backup-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}.json`;
}
