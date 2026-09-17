import { useMemo, useState } from 'react';
import { useStore } from './store';
import { computeProfit } from '../domain/profit';
import { suggestRiskFlags } from '../domain/risk';
import { DESTINATIONS } from '../domain/defaults';
import {
  FIELD_LABELS,
  guessMapping,
  parseCsvText,
  rowsToCandidates,
  type CanonicalField,
  type ColumnMapping,
  type ParsedCsv,
} from '../datasources/terapeakCsv';
import type { Candidate } from '../domain/types';
import { Field, NumberInput } from './components';
import { pct, roiText, usd, yen } from './format';

type Mode = 'manual' | 'csv';

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `c_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function AddCandidate({ onCreated }: { onCreated: (id: string) => void }) {
  const [mode, setMode] = useState<Mode>('manual');
  return (
    <>
      <div className="row" style={{ marginBottom: 12 }}>
        <button
          className={`btn ${mode === 'manual' ? '' : 'secondary'}`}
          style={{ flex: 1 }}
          onClick={() => setMode('manual')}
        >
          手動入力
        </button>
        <button
          className={`btn ${mode === 'csv' ? '' : 'secondary'}`}
          style={{ flex: 1 }}
          onClick={() => setMode('csv')}
        >
          Terapeak CSV
        </button>
      </div>
      {mode === 'manual' ? <ManualForm onCreated={onCreated} /> : <CsvImport />}
    </>
  );
}

function ManualForm({ onCreated }: { onCreated: (id: string) => void }) {
  const { settings, upsertCandidate, toast } = useStore();
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [sellPriceUsd, setSell] = useState<number | undefined>(undefined);
  const [costJpy, setCost] = useState<number | undefined>(undefined);
  const [weightG, setWeight] = useState<number | undefined>(500);
  const [destination, setDest] = useState(settings.defaultDestination);
  const [shipMethod, setShip] = useState(settings.defaultShipMethod);
  const [promoted, setPromoted] = useState(false);

  // 入力中もリアルタイムに着地利益を出す（これがこのツールの主目的）
  const preview = useMemo(
    () =>
      computeProfit(
        {
          sellPriceUsd: sellPriceUsd ?? 0,
          costJpy: costJpy ?? 0,
          weightG: weightG ?? 0,
          destination,
          shipMethod,
          promoted,
          category: category || undefined,
        },
        settings.rates,
        settings.shipping,
      ),
    [sellPriceUsd, costJpy, weightG, destination, shipMethod, promoted, category, settings],
  );

  const canSave = title.trim() !== '' && (sellPriceUsd ?? 0) > 0;

  async function save() {
    const now = new Date().toISOString();
    const id = newId();
    const suggested = suggestRiskFlags(`${title} ${category}`, settings.risk).map((s) => s.flag);
    const c: Candidate = {
      id,
      title: title.trim(),
      category: category || undefined,
      keyword: title.trim(),
      sellPriceUsd: sellPriceUsd ?? 0,
      costJpy: costJpy ?? 0,
      weightG: weightG ?? 0,
      destination,
      shipMethod,
      promoted,
      riskFlags: [],
      riskSuggested: suggested,
      watch: false,
      createdAt: now,
      updatedAt: now,
    };
    await upsertCandidate(c);
    toast('候補を追加しました');
    onCreated(id);
  }

  return (
    <>
      <div className="card">
        <h3>候補を手動で追加</h3>
        <Field label="商品名">
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例: Nintendo Game Boy Pocket" />
        </Field>
        <div className="grid-2" style={{ marginTop: 10 }}>
          <Field label="想定売値（USD）">
            <NumberInput value={sellPriceUsd} min={0} onChange={setSell} placeholder="120" />
          </Field>
          <Field label="仕入れ値（円・税込）">
            <NumberInput value={costJpy} min={0} onChange={setCost} placeholder="6000" />
          </Field>
          <Field label="重量（g・梱包込み）">
            <NumberInput value={weightG} min={0} onChange={setWeight} placeholder="500" />
          </Field>
          <Field label="カテゴリ（任意）">
            <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Video Games" />
          </Field>
          <Field label="仕向地">
            <select value={destination} onChange={(e) => setDest(e.target.value)}>
              {DESTINATIONS.map((d) => (
                <option key={d.code} value={d.code}>
                  {d.label}（{d.code}）
                </option>
              ))}
            </select>
          </Field>
          <Field label="発送方法">
            <select value={shipMethod} onChange={(e) => setShip(e.target.value)}>
              {Object.entries(settings.shipping.methods).map(([key, m]) => (
                <option key={key} value={key}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <label className="check">
          <input type="checkbox" checked={promoted} onChange={(e) => setPromoted(e.target.checked)} />
          販促キャンペーンを使う想定
        </label>
      </div>

      <div className="card">
        <h3>試算</h3>
        <div className="kv">
          <div>
            <span className="k">着地利益</span>
            <span className={`v ${preview.profitJpy >= 0 ? 'pos' : 'neg'}`} style={{ fontSize: 17 }}>
              {yen(preview.profitJpy)}
            </span>
          </div>
          <div>
            <span className="k">ROI</span>
            <span className="v">{roiText(preview.roi, costJpy ?? 0)}</span>
          </div>
          <div>
            <span className="k">マージン率</span>
            <span className="v">{pct(preview.marginRate)}</span>
          </div>
        </div>
        <div className="note" style={{ marginTop: 10 }}>
          売上 {yen(preview.revenueJpy)}（{usd(sellPriceUsd ?? 0)} × {preview.fx}円） − eBay手数料{' '}
          {yen(preview.ebayFeeJpy)} − 入金 {yen(preview.payoutFeeJpy)} − 仕入 {yen(preview.costJpy)} − 送料{' '}
          {yen(preview.shippingJpy)} − 雑費 {yen(preview.miscJpy)}
        </div>
        {!preview.shipping.found ? (
          <div className="alert warn" style={{ marginTop: 8 }}>
            送料が確定できません（{preview.shipping.reason}）。送料0円で試算しています。
          </div>
        ) : null}
        <button className="btn" style={{ marginTop: 12 }} disabled={!canSave} onClick={() => void save()}>
          この候補を保存
        </button>
        {!canSave ? <div className="note" style={{ marginTop: 6 }}>商品名と想定売値は必須です。</div> : null}
      </div>
    </>
  );
}

function CsvImport() {
  const { settings, addCandidates, toast } = useStore();
  const [parsed, setParsed] = useState<ParsedCsv | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping>({});
  const [error, setError] = useState<string | null>(null);
  const [periodDays, setPeriodDays] = useState<number | undefined>(90);
  const [weightG, setWeightG] = useState<number | undefined>(500);
  const [costJpy, setCostJpy] = useState<number | undefined>(0);

  const results = useMemo(() => {
    if (!parsed) return [];
    return rowsToCandidates(parsed.rows, mapping, {
      costJpy: costJpy ?? 0,
      weightG: weightG ?? 0,
      destination: settings.defaultDestination,
      shipMethod: settings.defaultShipMethod,
      promoted: false,
      periodDays: periodDays ?? 90,
    });
  }, [parsed, mapping, costJpy, weightG, periodDays, settings]);

  const made = results.filter((r) => r.candidate);
  const skipped = results.filter((r) => r.skipped);

  async function onFile(file: File) {
    setError(null);
    try {
      const text = await file.text();
      const p = parseCsvText(text);
      if (p.headers.length === 0) throw new Error('ヘッダ行を読み取れませんでした');
      setParsed(p);
      setMapping(guessMapping(p.headers));
    } catch (e) {
      setError((e as Error).message);
      setParsed(null);
    }
  }

  return (
    <>
      <div className="card">
        <h3>Terapeak CSV を取り込む</h3>
        <div className="note" style={{ marginBottom: 10 }}>
          Seller Hub → Product Research の検索結果を CSV エクスポートしたファイルを選んでください。
          スクレイピングは行いません。手元にダウンロード済みのファイルだけを読みます。
        </div>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void onFile(f);
          }}
        />
        {error ? <div className="alert error" style={{ marginTop: 10 }}>{error}</div> : null}
      </div>

      {parsed ? (
        <>
          <div className="card">
            <h3>列マッピング</h3>
            <div className="note" style={{ marginBottom: 10 }}>
              自動で推測しています。eBay側の列名が変わっていたらここで直してください。
            </div>
            {(Object.keys(FIELD_LABELS) as CanonicalField[]).map((field) => (
              <Field key={field} label={FIELD_LABELS[field]}>
                <select
                  value={mapping[field] ?? ''}
                  onChange={(e) =>
                    setMapping((m) => ({ ...m, [field]: e.target.value || undefined }))
                  }
                >
                  <option value="">（使わない）</option>
                  {parsed.headers.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </Field>
            ))}
          </div>

          <div className="card">
            <h3>取り込み時の既定値</h3>
            <div className="grid-2">
              <Field label="集計期間（日）" hint="Terapeakの検索期間。回転スコアの分母になります。">
                <NumberInput value={periodDays} min={1} onChange={setPeriodDays} />
              </Field>
              <Field label="重量（g）" hint="後から個別に直せます。">
                <NumberInput value={weightG} min={0} onChange={setWeightG} />
              </Field>
              <Field label="仕入れ値（円）" hint="0のままなら後で個別入力。">
                <NumberInput value={costJpy} min={0} onChange={setCostJpy} />
              </Field>
            </div>
          </div>

          <div className="card">
            <h3>プレビュー（{made.length} 件）</h3>
            {skipped.length > 0 ? (
              <div className="note" style={{ marginBottom: 8 }}>
                {skipped.length} 行はスキップされます（{skipped[0].skipped}）
              </div>
            ) : null}
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th style={{ cursor: 'default' }}>商品名</th>
                    <th style={{ cursor: 'default' }}>平均売値</th>
                    <th style={{ cursor: 'default' }}>販売数</th>
                    <th style={{ cursor: 'default' }}>STR</th>
                  </tr>
                </thead>
                <tbody>
                  {made.slice(0, 20).map((r) => (
                    <tr key={r.rowIndex} style={{ cursor: 'default' }}>
                      <td>{r.candidate!.title}</td>
                      <td className="mono">{usd(r.candidate!.demand?.avgSoldPriceUsd)}</td>
                      <td className="mono">{r.candidate!.demand?.soldCount ?? '—'}</td>
                      <td className="mono">{pct(r.candidate!.demand?.sellThroughRate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              className="btn"
              style={{ marginTop: 12 }}
              disabled={made.length === 0}
              onClick={async () => {
                await addCandidates(made.map((r) => r.candidate!));
                toast(`${made.length} 件を取り込みました`);
                setParsed(null);
              }}
            >
              {made.length} 件を取り込む
            </button>
          </div>
        </>
      ) : null}
    </>
  );
}
