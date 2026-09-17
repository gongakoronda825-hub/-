import { useEffect, useMemo, useState } from 'react';
import { useStore } from './store';
import { evaluate } from '../domain/evaluate';
import { breakEvenSellPriceUsd } from '../domain/profit';
import { priceDivergence } from '../domain/score';
import { RISK_LABELS, shippingWarnings } from '../domain/risk';
import { DESTINATIONS } from '../domain/defaults';
import { fetchBrowseStats, toMarketData } from '../datasources/browseApi';
import { searchSuppliers, type SupplierItem } from '../datasources/suppliers';
import { listSnapshots } from '../storage/db';
import type { Candidate, ManualRiskFlag, Snapshot } from '../domain/types';
import { Bar, Field, NumberInput, RiskBadges, ScorePill, Sparkline } from './components';
import { pct, roiText, shortDate, signedYen, usd, yen } from './format';

export function CandidateDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const { candidates, settings, upsertCandidate, removeCandidate, toast, snapshot } = useStore();
  const candidate = candidates.find((c) => c.id === id);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierItem[] | null>(null);
  const [history, setHistory] = useState<Snapshot[]>([]);

  useEffect(() => {
    if (!candidate) return;
    listSnapshots(candidate.id).then(setHistory).catch(() => setHistory([]));
  }, [candidate?.id]);

  const evaluated = useMemo(
    () => (candidate ? evaluate(candidate, settings) : null),
    [candidate, settings],
  );

  if (!candidate || !evaluated) {
    return (
      <div className="card">
        <p>候補が見つかりません（削除された可能性があります）。</p>
        <button className="btn secondary" onClick={onBack}>
          一覧に戻る
        </button>
      </div>
    );
  }

  const { profit: p, score, suggestedRisks: suggestions } = evaluated;
  const patch = (over: Partial<Candidate>) => void upsertCandidate({ ...candidate, ...over });

  const breakEven = breakEvenSellPriceUsd(
    {
      costJpy: candidate.costJpy,
      weightG: candidate.weightG,
      destination: candidate.destination,
      shipMethod: candidate.shipMethod,
      shippingOverrideJpy: candidate.shippingOverrideJpy,
      promoted: candidate.promoted,
      category: candidate.category,
    },
    settings.rates,
    settings.shipping,
    0,
  );

  const divergence = priceDivergence(candidate);
  const shipWarnings = shippingWarnings(score.activeFlags, candidate.shipMethod);
  const lastSnap = history.length > 0 ? history[history.length - 1] : null;

  async function withBusy(label: string, fn: () => Promise<void>) {
    setBusy(label);
    setError(null);
    setHint(null);
    try {
      await fn();
    } catch (e) {
      const err = e as Error & { hint?: string };
      setError(err.message);
      if (err.hint) setHint(err.hint);
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <div className="row between" style={{ marginBottom: 10 }}>
        <button className="btn secondary" onClick={onBack} style={{ width: 'auto' }}>
          ← 一覧
        </button>
        <label className="check">
          <input
            type="checkbox"
            checked={candidate.watch}
            onChange={(e) => patch({ watch: e.target.checked })}
          />
          ウォッチする
        </label>
      </div>

      {error ? (
        <div className="alert error">
          {error}
          {hint ? <div className="note" style={{ marginTop: 6 }}>{hint}</div> : null}
        </div>
      ) : null}

      {/* ---- サマリ ---- */}
      <div className="card">
        <div className="row between" style={{ alignItems: 'flex-start' }}>
          <h2 style={{ flex: 1 }}>{candidate.title}</h2>
          <ScorePill score={score.total} />
        </div>
        <div className="kv" style={{ marginTop: 4 }}>
          <div>
            <span className="k">着地利益</span>
            <span className={`v ${p.profitJpy >= 0 ? 'pos' : 'neg'}`} style={{ fontSize: 17 }}>
              {yen(p.profitJpy)}
            </span>
          </div>
          <div>
            <span className="k">ROI（対仕入れ）</span>
            <span className="v">{roiText(p.roi, candidate.costJpy)}</span>
          </div>
          <div>
            <span className="k">マージン率（対売上）</span>
            <span className="v">{pct(p.marginRate)}</span>
          </div>
        </div>
        <div className="row" style={{ marginTop: 10, gap: 4 }}>
          <RiskBadges flags={score.activeFlags} />
        </div>
        <div className="note" style={{ marginTop: 8 }}>
          損益分岐の売値：{usd(breakEven)}（この売値で着地利益 0 円）
        </div>
      </div>

      {/* ---- 入力 ---- */}
      <div className="card">
        <h3>入力</h3>
        <Field label="商品名">
          <input value={candidate.title} onChange={(e) => patch({ title: e.target.value })} />
        </Field>
        <div className="grid-2" style={{ marginTop: 10 }}>
          <Field label="想定売値（USD）">
            <NumberInput
              value={candidate.sellPriceUsd}
              min={0}
              onChange={(v) => patch({ sellPriceUsd: v ?? 0 })}
            />
          </Field>
          <Field label="仕入れ値（円・税込）">
            <NumberInput value={candidate.costJpy} min={0} onChange={(v) => patch({ costJpy: v ?? 0 })} />
          </Field>
          <Field label="重量（g・梱包込み）">
            <NumberInput value={candidate.weightG} min={0} onChange={(v) => patch({ weightG: v ?? 0 })} />
          </Field>
          <Field label="カテゴリ（手数料率に影響）">
            <input
              value={candidate.category ?? ''}
              list="category-list"
              placeholder="例: Video Games"
              onChange={(e) => patch({ category: e.target.value || undefined })}
            />
          </Field>
          <Field label="仕向地">
            <select value={candidate.destination} onChange={(e) => patch({ destination: e.target.value })}>
              {DESTINATIONS.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.label}（{d.code}）
                </option>
              ))}
            </select>
          </Field>
          <Field label="発送方法">
            <select value={candidate.shipMethod} onChange={(e) => patch({ shipMethod: e.target.value })}>
              {Object.entries(settings.shipping.methods).map(([key, m]) => (
                <option key={key} value={key}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="送料の手動指定（円・空欄で料金表）">
            <NumberInput
              value={candidate.shippingOverrideJpy ?? undefined}
              min={0}
              placeholder="料金表を使う"
              onChange={(v) => patch({ shippingOverrideJpy: v ?? null })}
            />
          </Field>
        </div>
        <datalist id="category-list">
          {Object.keys(settings.rates.ebay.category_final_value_rates ?? {})
            .filter((k) => k !== 'default')
            .map((k) => (
              <option key={k} value={k} />
            ))}
        </datalist>
        <label className="check">
          <input
            type="checkbox"
            checked={candidate.promoted}
            onChange={(e) => patch({ promoted: e.target.checked })}
          />
          販促キャンペーン（Promoted Listings）を使う想定
        </label>
      </div>

      {/* ---- 内訳 ---- */}
      <div className="card">
        <h3>着地利益の内訳</h3>
        <table className="breakdown">
          <tbody>
            <tr>
              <td>
                売上（{usd(candidate.sellPriceUsd)} × {p.fx}円）
              </td>
              <td className="mono">{yen(p.revenueJpy)}</td>
            </tr>
            <tr>
              <td>− 落札手数料（{pct(p.finalValueRate, 2)}）</td>
              <td className="mono neg">−{yen(p.finalValueJpy)}</td>
            </tr>
            <tr>
              <td>− 国際取引手数料（{pct(settings.rates.ebay.international_fee_rate, 2)}）</td>
              <td className="mono neg">−{yen(p.internationalFeeJpy)}</td>
            </tr>
            {candidate.promoted ? (
              <tr>
                <td>− 販促キャンペーン（{pct(settings.rates.ebay.promoted_rate, 2)}）</td>
                <td className="mono neg">−{yen(p.promotedJpy)}</td>
              </tr>
            ) : null}
            <tr>
              <td>− 注文固定手数料（${settings.rates.ebay.per_order_fixed_usd}）</td>
              <td className="mono neg">−{yen(p.perOrderFixedJpy)}</td>
            </tr>
            <tr>
              <td>− 入金・為替手数料（{pct(settings.rates.payout_fee_rate, 2)}）</td>
              <td className="mono neg">−{yen(p.payoutFeeJpy)}</td>
            </tr>
            <tr>
              <td>− 仕入れ値</td>
              <td className="mono neg">−{yen(p.costJpy)}</td>
            </tr>
            <tr>
              <td>
                − 国際送料（{settings.shipping.methods[candidate.shipMethod]?.label ?? candidate.shipMethod} /{' '}
                {p.shipping.zone}
                {p.shipping.bandMaxG ? ` / 〜${p.shipping.bandMaxG}g` : ''}）
              </td>
              <td className="mono neg">−{yen(p.shippingJpy)}</td>
            </tr>
            <tr>
              <td>− 雑費（梱包・国内送料）</td>
              <td className="mono neg">−{yen(p.miscJpy)}</td>
            </tr>
            <tr className="total">
              <td>着地利益（手取り）</td>
              <td className={`mono ${p.profitJpy >= 0 ? 'pos' : 'neg'}`}>{yen(p.profitJpy)}</td>
            </tr>
          </tbody>
        </table>
        {!p.shipping.found ? (
          <div className="alert warn" style={{ marginTop: 10 }}>
            送料を確定できませんでした（{p.shipping.reason}）。送料0円で計算しています。手動指定するか、
            設定の送料表を更新してください。
          </div>
        ) : null}
      </div>

      {/* ---- スコア内訳 ---- */}
      <div className="card">
        <h3>スコア内訳</h3>
        {(
          [
            ['需要', score.parts.demand, settings.scoring.weights.demand],
            ['利益', score.parts.profit, settings.scoring.weights.profit],
            ['回転', score.parts.turnover, settings.scoring.weights.turnover],
            ['競合', score.parts.competition, settings.scoring.weights.competition],
          ] as const
        ).map(([label, value, weight]) => (
          <div key={label} style={{ marginBottom: 10 }}>
            <div className="row between small">
              <span>
                {label} <span className="muted">（重み {weight}）</span>
              </span>
              <span className="mono">{Math.round(value)}</span>
            </div>
            <Bar value={value} />
          </div>
        ))}
        <div className="row between small">
          <span>
            リスク減点 <span className="muted">（重み {settings.scoring.weights.risk}）</span>
          </span>
          <span className="mono neg">−{Math.round(score.parts.riskPenalty * settings.scoring.weights.risk)}</span>
        </div>
        {score.missing.length > 0 ? (
          <div className="note" style={{ marginTop: 10 }}>
            未取得のデータ：{score.missing.join(' / ')}
            <br />
            欠損項目は重みごと分母から外して計算しています（0点扱いにはしません）。
          </div>
        ) : null}
      </div>

      {/* ---- 需要データ ---- */}
      <div className="card">
        <h3>需要データ（Terapeak / 手動）</h3>
        <div className="grid-2">
          <Field label="実売の平均価格（USD）">
            <NumberInput
              value={candidate.demand?.avgSoldPriceUsd}
              min={0}
              onChange={(v) =>
                patch({
                  demand: { ...(candidate.demand ?? { source: 'manual' }), avgSoldPriceUsd: v, source: candidate.demand?.source ?? 'manual' },
                })
              }
            />
          </Field>
          <Field label="販売数（期間内）">
            <NumberInput
              value={candidate.demand?.soldCount}
              min={0}
              onChange={(v) =>
                patch({
                  demand: { ...(candidate.demand ?? { source: 'manual' }), soldCount: v, source: candidate.demand?.source ?? 'manual' },
                })
              }
            />
          </Field>
          <Field label="sell-through率（%）">
            <NumberInput
              value={
                candidate.demand?.sellThroughRate != null
                  ? Math.round(candidate.demand.sellThroughRate * 1000) / 10
                  : undefined
              }
              min={0}
              onChange={(v) =>
                patch({
                  demand: {
                    ...(candidate.demand ?? { source: 'manual' }),
                    sellThroughRate: v == null ? undefined : v / 100,
                    source: candidate.demand?.source ?? 'manual',
                  },
                })
              }
            />
          </Field>
          <Field label="集計期間（日）">
            <NumberInput
              value={candidate.demand?.periodDays}
              min={1}
              onChange={(v) =>
                patch({
                  demand: { ...(candidate.demand ?? { source: 'manual' }), periodDays: v, source: candidate.demand?.source ?? 'manual' },
                })
              }
            />
          </Field>
        </div>
        <div className="note" style={{ marginTop: 8 }}>
          出所：{candidate.demand?.source === 'terapeak-csv' ? 'Terapeak CSV' : '手動入力'}
          {candidate.demand?.fetchedAt ? ` / ${shortDate(candidate.demand.fetchedAt)}` : ''}
        </div>
      </div>

      {/* ---- 出品中の相場（Browse API） ---- */}
      <div className="card">
        <h3>出品中の相場・競合（Browse API）</h3>
        <Field label="検索キーワード">
          <input
            value={candidate.keyword ?? candidate.title}
            onChange={(e) => patch({ keyword: e.target.value })}
          />
        </Field>
        <button
          className="btn secondary"
          style={{ marginTop: 10 }}
          disabled={busy != null}
          onClick={() =>
            withBusy('browse', async () => {
              const stats = await fetchBrowseStats(settings.apiBase, {
                q: candidate.keyword || candidate.title,
              });
              await upsertCandidate({ ...candidate, market: toMarketData(stats) });
              toast(`出品中 ${stats.activeCount} 件を取得しました`);
            })
          }
        >
          {busy === 'browse' ? '取得中…' : '出品中の相場を取得'}
        </button>

        {candidate.market ? (
          <>
            <div className="kv" style={{ marginTop: 12 }}>
              <div>
                <span className="k">出品中</span>
                <span className="v">{candidate.market.activeCount ?? '—'} 件</span>
              </div>
              <div>
                <span className="k">中央値</span>
                <span className="v">{usd(candidate.market.medianUsd)}</span>
              </div>
              <div>
                <span className="k">25% / 75%</span>
                <span className="v">
                  {usd(candidate.market.p25Usd)} / {usd(candidate.market.p75Usd)}
                </span>
              </div>
            </div>
            <div className="note" style={{ marginTop: 8 }}>
              取得 {shortDate(candidate.market.fetchedAt)}。Browse API が返すのは出品中のみで、売れた実績ではありません。
            </div>
            {candidate.market.medianUsd ? (
              <button
                className="link"
                onClick={() => patch({ sellPriceUsd: Number(candidate.market!.medianUsd!.toFixed(2)) })}
              >
                想定売値を中央値 {usd(candidate.market.medianUsd)} にする
              </button>
            ) : null}
          </>
        ) : (
          <div className="note" style={{ marginTop: 8 }}>
            未取得。競合スコアはこのデータが入ると有効になります。
          </div>
        )}

        {divergence ? (
          <div className={Math.abs(divergence.rate) > 0.25 ? 'alert warn' : 'note'} style={{ marginTop: 10 }}>
            {divergence.note}
          </div>
        ) : null}
      </div>

      {/* ---- 仕入れ元 ---- */}
      <div className="card">
        <h3>仕入れ元</h3>
        <button
          className="btn secondary"
          disabled={busy != null}
          onClick={() =>
            withBusy('suppliers', async () => {
              const { items, errors } = await searchSuppliers(
                settings.apiBase,
                candidate.keyword || candidate.title,
              );
              setSuppliers(items);
              if (items.length === 0 && errors.length > 0) throw new Error(errors.join(' / '));
              if (errors.length > 0) toast(errors.join(' / '));
            })
          }
        >
          {busy === 'suppliers' ? '検索中…' : '楽天 / Yahoo!ショッピングで仕入れ候補を検索'}
        </button>
        <div className="note" style={{ marginTop: 8 }}>
          メルカリ・ヤフオク・駿河屋などは公式APIが無いため自動取得しません。URLと価格を下に手動で貼り付けてください。
        </div>

        {suppliers && suppliers.length > 0 ? (
          <div style={{ marginTop: 10 }}>
            {suppliers.slice(0, 12).map((s, i) => (
              <div key={`${s.url}-${i}`} className="supplier-item">
                {s.imageUrl ? <img src={s.imageUrl} alt="" loading="lazy" /> : null}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="small" style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.title}
                  </div>
                  <div className="small muted">
                    {yen(s.priceJpy)} / {s.source === 'rakuten' ? '楽天' : 'Yahoo!'}
                    {s.shop ? ` / ${s.shop}` : ''}
                  </div>
                </div>
                <button
                  className="link"
                  onClick={() =>
                    patch({
                      costJpy: s.priceJpy,
                      suppliers: [
                        ...(candidate.suppliers ?? []),
                        { name: s.title, url: s.url, priceJpy: s.priceJpy, source: s.source },
                      ],
                    })
                  }
                >
                  原価に採用
                </button>
              </div>
            ))}
          </div>
        ) : null}

        <Field label="仕入れ元メモ / URL（手動）">
          <textarea
            rows={3}
            value={candidate.notes ?? ''}
            placeholder="メルカリやヤフオクのURL・価格・状態などを貼り付け"
            onChange={(e) => patch({ notes: e.target.value })}
          />
        </Field>
        {candidate.suppliers && candidate.suppliers.length > 0 ? (
          <div className="note" style={{ marginTop: 8 }}>
            採用履歴：
            {candidate.suppliers.slice(-3).map((s, i) => (
              <div key={i}>
                {yen(s.priceJpy)}{' '}
                {s.url ? (
                  <a href={s.url} target="_blank" rel="noreferrer">
                    {s.name.slice(0, 40)}
                  </a>
                ) : (
                  s.name
                )}
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* ---- リスク ---- */}
      <div className="card">
        <h3>リスク / 規制チェック</h3>
        {suggestions.length > 0 ? (
          <div className="alert warn">
            キーワードから該当の可能性：
            {suggestions.map((f) => RISK_LABELS[f]).join(' / ')}
            <div className="note" style={{ marginTop: 6 }}>
              自動判定は当たりを付けるだけです。下のチェックで確定してください。
            </div>
          </div>
        ) : null}
        {(Object.keys(RISK_LABELS) as (keyof typeof RISK_LABELS)[])
          .filter((f) => f !== 'low_ticket' && f !== 'thin_margin' && f !== 'category_restricted')
          .map((f) => (
            <label key={f} className="check">
              <input
                type="checkbox"
                checked={candidate.riskFlags.includes(f as ManualRiskFlag)}
                onChange={(e) => {
                  const flag = f as ManualRiskFlag;
                  patch({
                    riskFlags: e.target.checked
                      ? [...candidate.riskFlags, flag]
                      : candidate.riskFlags.filter((x) => x !== flag),
                  });
                }}
              />
              {RISK_LABELS[f]}
              {suggestions.includes(f as ManualRiskFlag) ? <span className="badge warn">候補</span> : null}
            </label>
          ))}
        <label className="check">
          <input
            type="checkbox"
            checked={candidate.categoryRestricted ?? false}
            onChange={(e) => patch({ categoryRestricted: e.target.checked })}
          />
          {RISK_LABELS.category_restricted}
        </label>
        {shipWarnings.map((w, i) => (
          <div key={i} className="alert warn" style={{ marginTop: 8 }}>
            {w}
          </div>
        ))}
      </div>

      {/* ---- 履歴 ---- */}
      <div className="card">
        <h3>履歴</h3>
        <div className="row">
          <button
            className="btn secondary"
            disabled={busy != null}
            onClick={() =>
              withBusy('snap', async () => {
                const snap = await snapshot(candidate);
                setHistory((h) => [...h, snap]);
                toast('現在値を記録しました');
              })
            }
          >
            現在値を記録
          </button>
        </div>
        {lastSnap ? (
          <div className="note" style={{ marginTop: 10 }}>
            前回記録（{shortDate(lastSnap.at)}）比：
            <span className={p.profitJpy - lastSnap.profitJpy >= 0 ? 'pos' : 'neg'}>
              {' '}
              {signedYen(p.profitJpy - lastSnap.profitJpy)}
            </span>
          </div>
        ) : (
          <div className="note" style={{ marginTop: 10 }}>
            記録はまだありません。ウォッチリストの「一括再計算」でも記録されます。
          </div>
        )}
        {history.length >= 2 ? (
          <>
            <Sparkline values={history.map((h) => h.profitJpy)} />
            <div className="note">着地利益の推移（{history.length} 点）</div>
          </>
        ) : null}
      </div>

      <div className="card">
        <button
          className="btn danger"
          onClick={() => {
            if (confirm('この候補を削除します。よろしいですか？')) {
              void removeCandidate(candidate.id);
              onBack();
            }
          }}
        >
          この候補を削除
        </button>
      </div>
    </>
  );
}
