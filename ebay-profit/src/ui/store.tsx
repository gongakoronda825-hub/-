import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { AppSettings, Candidate, Snapshot } from '../domain/types';
import * as store from '../storage/db';
import { fetchFx } from '../datasources/fx';
import { defaultSettings } from '../domain/defaults';
import { evaluate } from '../domain/evaluate';

interface StoreValue {
  ready: boolean;
  settings: AppSettings;
  candidates: Candidate[];
  toastMsg: string | null;
  toast: (msg: string) => void;
  updateSettings: (s: AppSettings) => Promise<void>;
  resetSettings: () => Promise<void>;
  upsertCandidate: (c: Candidate) => Promise<void>;
  addCandidates: (list: Candidate[]) => Promise<void>;
  removeCandidate: (id: string) => Promise<void>;
  reload: () => Promise<void>;
  refreshFx: () => Promise<void>;
  /** 現在値でスナップショットを1件記録する（ウォッチリストの再計算） */
  snapshot: (c: Candidate) => Promise<Snapshot>;
}

const Ctx = createContext<StoreValue | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [settings, setSettings] = useState<AppSettings>(() => defaultSettings());
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const toast = useCallback((msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg((cur) => (cur === msg ? null : cur)), 2600);
  }, []);

  const reload = useCallback(async () => {
    const [s, list] = await Promise.all([store.loadSettings(), store.listCandidates()]);
    setSettings(s);
    setCandidates(list);
  }, []);

  useEffect(() => {
    reload()
      .catch((e) => console.error('初期読み込みに失敗', e))
      .finally(() => setReady(true));
  }, [reload]);

  const updateSettings = useCallback(async (s: AppSettings) => {
    await store.saveSettings(s);
    setSettings(s);
  }, []);

  const resetSettings = useCallback(async () => {
    const s = await store.resetSettings();
    setSettings(s);
  }, []);

  const upsertCandidate = useCallback(async (c: Candidate) => {
    const withStamp = { ...c, updatedAt: new Date().toISOString() };
    await store.putCandidate(withStamp);
    setCandidates((prev) => {
      const i = prev.findIndex((p) => p.id === withStamp.id);
      if (i === -1) return [...prev, withStamp];
      const next = [...prev];
      next[i] = withStamp;
      return next;
    });
  }, []);

  const addCandidates = useCallback(async (list: Candidate[]) => {
    await store.putCandidates(list);
    setCandidates((prev) => [...prev, ...list]);
  }, []);

  const removeCandidate = useCallback(async (id: string) => {
    await store.deleteCandidate(id);
    setCandidates((prev) => prev.filter((c) => c.id !== id));
  }, []);

  const refreshFx = useCallback(async () => {
    const current = await store.loadSettings();
    if (current.rates.fx_manual_override) {
      throw new Error('為替は手動固定中です（設定画面で解除できます）');
    }
    const fx = await fetchFx(current.apiBase);
    const next: AppSettings = {
      ...current,
      rates: { ...current.rates, fx_jpy_per_usd: fx.jpyPerUsd, fx_updated_at: fx.fetchedAt },
    };
    await store.saveSettings(next);
    setSettings(next);
  }, []);

  const snapshot = useCallback(
    async (c: Candidate) => {
      const { profit, score } = evaluate(c, settings);
      const snap: Snapshot = {
        candidateId: c.id,
        at: new Date().toISOString(),
        fx: profit.fx,
        sellPriceUsd: c.sellPriceUsd,
        costJpy: c.costJpy,
        profitJpy: profit.profitJpy,
        roi: profit.roi,
        score: score.total,
        marketMedianUsd: c.market?.medianUsd,
        activeCount: c.market?.activeCount,
      };
      await store.addSnapshot(snap);
      return snap;
    },
    [settings],
  );

  const value = useMemo<StoreValue>(
    () => ({
      ready,
      settings,
      candidates,
      toastMsg,
      toast,
      updateSettings,
      resetSettings,
      upsertCandidate,
      addCandidates,
      removeCandidate,
      reload,
      refreshFx,
      snapshot,
    }),
    [
      ready,
      settings,
      candidates,
      toastMsg,
      toast,
      updateSettings,
      resetSettings,
      upsertCandidate,
      addCandidates,
      removeCandidate,
      reload,
      refreshFx,
      snapshot,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useStore(): StoreValue {
  const v = useContext(Ctx);
  if (!v) throw new Error('StoreProvider の外で useStore が呼ばれました');
  return v;
}
