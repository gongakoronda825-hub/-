import { useCallback, useEffect, useState } from 'react';
import { useStore } from './store';
import { evaluate } from '../domain/evaluate';
import { listSnapshots } from '../storage/db';
import type { Snapshot } from '../domain/types';
import { Empty, ScorePill } from './components';
import { pct, shortDate, signedYen, yen } from './format';

interface RowState {
  last?: Snapshot;
  prev?: Snapshot;
}

export function Watchlist({ onOpen }: { onOpen: (id: string) => void }) {
  const { candidates, settings, snapshot, refreshFx, toast } = useStore();
  const watched = candidates.filter((c) => c.watch);
  const [snaps, setSnaps] = useState<Record<string, RowState>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSnaps = useCallback(async () => {
    const entries = await Promise.all(
      watched.map(async (c) => {
        const list = await listSnapshots(c.id);
        return [c.id, { last: list[list.length - 1], prev: list[list.length - 2] }] as const;
      }),
    );
    setSnaps(Object.fromEntries(entries));
  }, [watched.map((c) => c.id).join(',')]);

  useEffect(() => {
    void loadSnaps();
  }, [loadSnaps]);

  async function recalcAll() {
    setBusy(true);
    setError(null);
    try {
      // 為替は取れなければ現在値のまま続行する（オフラインでも再計算は成立する）
      try {
        await refreshFx();
      } catch (e) {
        setError(`為替の更新に失敗（現在値のまま再計算します）: ${(e as Error).message}`);
      }
      for (const c of watched) await snapshot(c);
      await loadSnaps();
      toast(`${watched.length} 件を再計算しました`);
    } finally {
      setBusy(false);
    }
  }

  if (watched.length === 0) {
    return (
      <Empty title="ウォッチ中の候補はありません">
        候補詳細の「ウォッチする」をオンにすると、ここに並びます。
        <br />
        再計算すると、そのときの為替・相場での着地利益が記録され、前回との差分が出ます。
      </Empty>
    );
  }

  return (
    <>
      <div className="card">
        <div className="row between">
          <div>
            <div style={{ fontWeight: 700 }}>ウォッチリスト {watched.length} 件</div>
            <div className="note">
              1USD = {settings.rates.fx_jpy_per_usd} 円
              {settings.rates.fx_updated_at ? `（${shortDate(settings.rates.fx_updated_at)}）` : ''}
            </div>
          </div>
          <button className="btn" style={{ width: 'auto' }} disabled={busy} onClick={() => void recalcAll()}>
            {busy ? '再計算中…' : '一括再計算'}
          </button>
        </div>
        {error ? <div className="alert warn" style={{ marginTop: 10 }}>{error}</div> : null}
      </div>

      {watched.map((c) => {
        const { profit, score } = evaluate(c, settings);
        const s = snaps[c.id];
        const base = s?.last;
        const delta = base ? profit.profitJpy - base.profitJpy : null;
        const alerts: string[] = [];
        const a = settings.scoring.alerts;
        if (profit.profitJpy < a.min_profit_jpy) alerts.push(`着地利益が下限 ${yen(a.min_profit_jpy)} を下回っています`);
        if (profit.roi < a.min_roi) alerts.push(`ROIが下限 ${pct(a.min_roi, 0)} を下回っています`);
        if (base && base.profitJpy > 0 && delta != null && delta / base.profitJpy <= -a.profit_drop_rate) {
          alerts.push(`前回記録から ${pct(Math.abs(delta / base.profitJpy), 0)} 減っています`);
        }

        return (
          <div key={c.id} className="cand-card" onClick={() => onOpen(c.id)}>
            <div className="row between" style={{ alignItems: 'flex-start' }}>
              <div className="title" style={{ flex: 1 }}>
                {c.title}
              </div>
              <ScorePill score={score.total} />
            </div>
            <div className="kv">
              <div>
                <span className="k">着地利益</span>
                <span className={`v ${profit.profitJpy >= 0 ? 'pos' : 'neg'}`}>{yen(profit.profitJpy)}</span>
              </div>
              <div>
                <span className="k">前回比</span>
                <span className={`v ${delta == null ? 'muted' : delta >= 0 ? 'pos' : 'neg'}`}>
                  {delta == null ? '記録なし' : signedYen(delta)}
                </span>
              </div>
              <div>
                <span className="k">最終記録</span>
                <span className="v small">{base ? shortDate(base.at) : '—'}</span>
              </div>
            </div>
            {alerts.map((msg, i) => (
              <div key={i} className="alert warn" style={{ marginTop: 8, marginBottom: 0 }}>
                {msg}
              </div>
            ))}
          </div>
        );
      })}
    </>
  );
}
