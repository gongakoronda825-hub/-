import { useMemo, useState } from 'react';
import { useStore } from './store';
import { evaluateAll, type Evaluated } from '../domain/evaluate';
import { roiText, usd, yen } from './format';
import { Empty, RiskBadges, ScorePill } from './components';

type SortKey = 'score' | 'profit' | 'roi' | 'sell' | 'cost' | 'turnover' | 'competition' | 'title';

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'title', label: '候補' },
  { key: 'score', label: 'スコア' },
  { key: 'sell', label: '想定売値' },
  { key: 'cost', label: '仕入' },
  { key: 'profit', label: '着地利益' },
  { key: 'roi', label: 'ROI' },
  { key: 'turnover', label: '回転' },
  { key: 'competition', label: '競合' },
];

function sortValue(e: Evaluated, key: SortKey): number | string {
  switch (key) {
    case 'title':
      return e.candidate.title;
    case 'score':
      return e.score.total;
    case 'profit':
      return e.profit.profitJpy;
    case 'roi':
      return e.profit.roi;
    case 'sell':
      return e.candidate.sellPriceUsd;
    case 'cost':
      return e.candidate.costJpy;
    case 'turnover':
      return e.score.parts.turnover;
    case 'competition':
      return -(e.candidate.market?.activeCount ?? Number.POSITIVE_INFINITY);
  }
}

export function Dashboard({ onOpen }: { onOpen: (id: string) => void }) {
  const { candidates, settings } = useStore();
  const [sortKey, setSortKey] = useState<SortKey>('score');
  const [asc, setAsc] = useState(false);
  const [query, setQuery] = useState('');
  const [minProfit, setMinProfit] = useState('');
  const [minRoi, setMinRoi] = useState('');
  const [hideRisky, setHideRisky] = useState(false);
  const [watchOnly, setWatchOnly] = useState(false);

  const rows = useMemo(() => {
    let list = evaluateAll(candidates, settings);

    const q = query.trim().toLowerCase();
    if (q) list = list.filter((e) => e.candidate.title.toLowerCase().includes(q));
    const mp = Number(minProfit);
    if (minProfit !== '' && Number.isFinite(mp)) list = list.filter((e) => e.profit.profitJpy >= mp);
    const mr = Number(minRoi);
    if (minRoi !== '' && Number.isFinite(mr)) list = list.filter((e) => e.profit.roi >= mr / 100);
    if (hideRisky) {
      list = list.filter(
        (e) => !e.score.activeFlags.some((f) => f !== 'low_ticket' && f !== 'thin_margin'),
      );
    }
    if (watchOnly) list = list.filter((e) => e.candidate.watch);

    return [...list].sort((a, b) => {
      const va = sortValue(a, sortKey);
      const vb = sortValue(b, sortKey);
      const cmp =
        typeof va === 'string' || typeof vb === 'string'
          ? String(va).localeCompare(String(vb), 'ja')
          : va - vb;
      return asc ? cmp : -cmp;
    });
  }, [candidates, settings, sortKey, asc, query, minProfit, minRoi, hideRisky, watchOnly]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setAsc((v) => !v);
    else {
      setSortKey(key);
      setAsc(key === 'title');
    }
  }

  if (candidates.length === 0) {
    return (
      <Empty title="候補がまだありません">
        「追加」タブから手入力するか、Terapeak の CSV を取り込んでください。
        <br />
        データ源がゼロでも、想定売値と仕入れ値を入れれば着地利益は出ます。
      </Empty>
    );
  }

  return (
    <>
      <div className="card">
        <input
          type="search"
          placeholder="候補を検索"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="grid-2" style={{ marginTop: 10 }}>
          <label className="field">
            <span>着地利益 下限（円）</span>
            <input
              type="text"
              inputMode="numeric"
              value={minProfit}
              placeholder="例: 1000"
              onChange={(e) => setMinProfit(e.target.value)}
            />
          </label>
          <label className="field">
            <span>ROI 下限（%）</span>
            <input
              type="text"
              inputMode="numeric"
              value={minRoi}
              placeholder="例: 30"
              onChange={(e) => setMinRoi(e.target.value)}
            />
          </label>
        </div>
        <div className="row" style={{ marginTop: 6 }}>
          <label className="check">
            <input type="checkbox" checked={hideRisky} onChange={(e) => setHideRisky(e.target.checked)} />
            規制/VeRO該当を隠す
          </label>
          <label className="check">
            <input type="checkbox" checked={watchOnly} onChange={(e) => setWatchOnly(e.target.checked)} />
            ウォッチのみ
          </label>
        </div>
        <div className="note" style={{ marginTop: 4 }}>
          {rows.length} 件 / 全 {candidates.length} 件（1USD = {settings.rates.fx_jpy_per_usd} 円で計算）
        </div>
      </div>

      {/* モバイル: カード表示 */}
      <div className="hide-desktop">
        <div className="row between" style={{ marginBottom: 8 }}>
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            style={{ width: 'auto', flex: 1 }}
            aria-label="並べ替え"
          >
            {COLUMNS.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}で並べ替え
              </option>
            ))}
          </select>
          <button className="btn secondary" onClick={() => setAsc((v) => !v)} style={{ width: 'auto' }}>
            {asc ? '昇順' : '降順'}
          </button>
        </div>
        {rows.map((e) => (
          <div key={e.candidate.id} className="cand-card" onClick={() => onOpen(e.candidate.id)}>
            <div className="row between" style={{ alignItems: 'flex-start' }}>
              <div className="title" style={{ flex: 1 }}>
                {e.candidate.watch ? '★ ' : ''}
                {e.candidate.title}
              </div>
              <ScorePill score={e.score.total} />
            </div>
            <div className="kv">
              <div>
                <span className="k">着地利益</span>
                <span className={`v ${e.profit.profitJpy >= 0 ? 'pos' : 'neg'}`}>
                  {yen(e.profit.profitJpy)}
                </span>
              </div>
              <div>
                <span className="k">ROI</span>
                <span className="v">{roiText(e.profit.roi, e.candidate.costJpy)}</span>
              </div>
              <div>
                <span className="k">売値 / 仕入</span>
                <span className="v">
                  {usd(e.candidate.sellPriceUsd)} / {yen(e.candidate.costJpy)}
                </span>
              </div>
            </div>
            <div className="row" style={{ marginTop: 8, gap: 4 }}>
              <RiskBadges flags={e.score.activeFlags} />
              {e.candidate.costJpy <= 0 ? <span className="badge warn">仕入未入力</span> : null}
              {e.suggestedRisks.length > 0 ? <span className="badge warn">リスク要確認</span> : null}
              {e.score.missing.length > 0 ? (
                <span className="badge">データ不足 {e.score.missing.length}</span>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      {/* PC: テーブル表示 */}
      <div className="hide-mobile table-wrap">
        <table>
          <thead>
            <tr>
              {COLUMNS.map((c) => (
                <th key={c.key} onClick={() => toggleSort(c.key)}>
                  {c.label}
                  {sortKey === c.key ? (asc ? ' ▲' : ' ▼') : ''}
                </th>
              ))}
              <th style={{ cursor: 'default' }}>リスク</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.candidate.id} onClick={() => onOpen(e.candidate.id)}>
                <td>
                  {e.candidate.watch ? '★ ' : ''}
                  {e.candidate.title}
                </td>
                <td className="mono">{Math.round(e.score.total)}</td>
                <td className="mono">{usd(e.candidate.sellPriceUsd)}</td>
                <td className="mono">{yen(e.candidate.costJpy)}</td>
                <td className={`mono ${e.profit.profitJpy >= 0 ? 'pos' : 'neg'}`}>
                  {yen(e.profit.profitJpy)}
                </td>
                <td className="mono">{roiText(e.profit.roi, e.candidate.costJpy)}</td>
                <td className="mono">
                  {e.candidate.demand?.soldCount != null && e.candidate.demand?.periodDays
                    ? `${((e.candidate.demand.soldCount / e.candidate.demand.periodDays) * 30).toFixed(1)}/月`
                    : '—'}
                </td>
                <td className="mono">{e.candidate.market?.activeCount ?? '—'}</td>
                <td style={{ textAlign: 'left' }}>
                  <RiskBadges flags={e.score.activeFlags} />
                  {e.candidate.costJpy <= 0 ? <span className="badge warn">仕入未入力</span> : null}
                  {e.suggestedRisks.length > 0 ? <span className="badge warn">要確認</span> : null}
                  {e.score.missing.length > 0 ? (
                    <span className="badge">データ不足 {e.score.missing.length}</span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
