import { useState } from 'react';
import { useStore } from './store';
import { Field, NumberInput } from './components';
import { shortDate } from './format';
import {
  backupFilename,
  buildBackup,
  downloadJson,
  restoreBackup,
  validateBackup,
  type RestoreMode,
} from '../storage/backup';
import type { AppSettings, ShippingTable } from '../domain/types';

export function Settings() {
  const { settings, updateSettings, resetSettings, reload, refreshFx, toast } = useStore();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [restoreMode, setRestoreMode] = useState<RestoreMode>('merge');

  const patch = (over: Partial<AppSettings>) => void updateSettings({ ...settings, ...over });
  const patchRates = (over: Partial<AppSettings['rates']>) =>
    patch({ rates: { ...settings.rates, ...over } });
  const patchEbay = (over: Partial<AppSettings['rates']['ebay']>) =>
    patchRates({ ebay: { ...settings.rates.ebay, ...over } });
  const patchScoring = (over: Partial<AppSettings['scoring']>) =>
    patch({ scoring: { ...settings.scoring, ...over } });

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
      {error ? (
        <div className="alert error">
          {error}
          {hint ? <div className="note" style={{ marginTop: 6 }}>{hint}</div> : null}
        </div>
      ) : null}

      {/* ---- 為替 ---- */}
      <div className="card">
        <h3>為替</h3>
        <div className="grid-2">
          <Field label="1 USD = ? 円">
            <NumberInput
              value={settings.rates.fx_jpy_per_usd}
              min={0}
              onChange={(v) => patchRates({ fx_jpy_per_usd: v ?? 0 })}
            />
          </Field>
        </div>
        <label className="check">
          <input
            type="checkbox"
            checked={settings.rates.fx_manual_override ?? false}
            onChange={(e) => patchRates({ fx_manual_override: e.target.checked })}
          />
          手動固定（自動更新を止める）
        </label>
        <div className="row" style={{ marginTop: 8 }}>
          <button
            className="btn secondary"
            disabled={busy != null}
            onClick={() =>
              withBusy('fx', async () => {
                await refreshFx();
                toast('為替を更新しました');
              })
            }
          >
            {busy === 'fx' ? '取得中…' : '為替を取得'}
          </button>
        </div>
        <div className="note" style={{ marginTop: 8 }}>
          最終更新：{shortDate(settings.rates.fx_updated_at)}
        </div>
      </div>

      {/* ---- eBay 手数料 ---- */}
      <div className="card">
        <h3>eBay 手数料・その他コスト</h3>
        <div className="note" style={{ marginBottom: 10 }}>
          初期値は雛形です。現行の料金表・カテゴリ別料率を確認して上書きしてください。率は小数（例: 13.25% → 0.1325）。
        </div>
        <div className="grid-2">
          <Field label="落札手数料率（既定）">
            <NumberInput
              value={settings.rates.ebay.final_value_rate}
              min={0}
              onChange={(v) => patchEbay({ final_value_rate: v ?? 0 })}
            />
          </Field>
          <Field label="国際取引手数料率">
            <NumberInput
              value={settings.rates.ebay.international_fee_rate}
              min={0}
              onChange={(v) => patchEbay({ international_fee_rate: v ?? 0 })}
            />
          </Field>
          <Field label="販促キャンペーン率">
            <NumberInput
              value={settings.rates.ebay.promoted_rate}
              min={0}
              onChange={(v) => patchEbay({ promoted_rate: v ?? 0 })}
            />
          </Field>
          <Field label="注文固定手数料（USD）">
            <NumberInput
              value={settings.rates.ebay.per_order_fixed_usd}
              min={0}
              onChange={(v) => patchEbay({ per_order_fixed_usd: v ?? 0 })}
            />
          </Field>
          <Field label="入金・為替手数料率">
            <NumberInput
              value={settings.rates.payout_fee_rate}
              min={0}
              onChange={(v) => patchRates({ payout_fee_rate: v ?? 0 })}
            />
          </Field>
          <Field label="雑費（円/個）" hint="梱包資材・国内送料など">
            <NumberInput
              value={settings.rates.misc_jpy_per_item}
              min={0}
              onChange={(v) => patchRates({ misc_jpy_per_item: v ?? 0 })}
            />
          </Field>
        </div>
        <JsonEditor
          label="カテゴリ別の落札手数料率"
          value={settings.rates.ebay.category_final_value_rates ?? { default: settings.rates.ebay.final_value_rate }}
          onSave={(v) => patchEbay({ category_final_value_rates: v as Record<string, number> })}
        />
      </div>

      {/* ---- 送料表 ---- */}
      <div className="card">
        <h3>国際送料表</h3>
        <div className="note" style={{ marginBottom: 10 }}>
          発送方法 × ゾーン × 重量帯（max_g 昇順）で円を返します。各社の現行料金表で更新してください。
        </div>
        <ShippingSummary table={settings.shipping} />
        <JsonEditor
          label="送料表（JSON）"
          value={settings.shipping}
          onSave={(v) => {
            const t = v as ShippingTable;
            if (!t.methods || typeof t.methods !== 'object') throw new Error('methods がありません');
            if (!t.zone_of_country) throw new Error('zone_of_country がありません');
            patch({ shipping: t });
          }}
        />
      </div>

      {/* ---- スコアリング ---- */}
      <div className="card">
        <h3>スコアリング</h3>
        <div className="grid-2">
          {(
            [
              ['demand', '需要の重み'],
              ['profit', '利益の重み'],
              ['turnover', '回転の重み'],
              ['competition', '競合の重み'],
              ['risk', 'リスク減点の重み'],
            ] as const
          ).map(([key, label]) => (
            <Field key={key} label={label}>
              <NumberInput
                value={settings.scoring.weights[key]}
                min={0}
                onChange={(v) =>
                  patchScoring({ weights: { ...settings.scoring.weights, [key]: v ?? 0 } })
                }
              />
            </Field>
          ))}
        </div>
        <JsonEditor
          label="スコア基準値・リスク減点・アラート（JSON）"
          value={{
            demand: settings.scoring.demand,
            profit: settings.scoring.profit,
            turnover: settings.scoring.turnover,
            competition: settings.scoring.competition,
            risk: settings.scoring.risk,
            alerts: settings.scoring.alerts,
          }}
          onSave={(v) => patchScoring(v as Partial<AppSettings['scoring']>)}
        />
      </div>

      {/* ---- API ---- */}
      <div className="card">
        <h3>外部API</h3>
        <Field
          label="APIベースURL"
          hint="サーバーレス関数のパス。既定は同一オリジンの /api。APIキーはサーバー側の環境変数に置き、この画面には入れません。"
        >
          <input value={settings.apiBase} onChange={(e) => patch({ apiBase: e.target.value })} />
        </Field>
        <div className="note" style={{ marginTop: 10 }}>
          ホスティング先に設定する環境変数：
          <br />
          <code>EBAY_CLIENT_ID</code> / <code>EBAY_CLIENT_SECRET</code>（Browse API）
          <br />
          <code>RAKUTEN_APP_ID</code>（楽天）、<code>YAHOO_APP_ID</code>（Yahoo!ショッピング）
          <br />
          為替はキー不要です。
        </div>
      </div>

      {/* ---- 既定値 ---- */}
      <div className="card">
        <h3>入力の既定値</h3>
        <div className="grid-2">
          <Field label="既定の仕向地">
            <input
              value={settings.defaultDestination}
              onChange={(e) => patch({ defaultDestination: e.target.value.toUpperCase() })}
            />
          </Field>
          <Field label="既定の発送方法">
            <select
              value={settings.defaultShipMethod}
              onChange={(e) => patch({ defaultShipMethod: e.target.value })}
            >
              {Object.entries(settings.shipping.methods).map(([key, m]) => (
                <option key={key} value={key}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
      </div>

      {/* ---- バックアップ ---- */}
      <div className="card">
        <h3>バックアップ / 復元</h3>
        <div className="note" style={{ marginBottom: 10 }}>
          データは端末内（IndexedDB）にのみ保存されます。iPhone では「ホーム画面に追加」しておかないと
          数日で消えることがあります。定期的にJSONへ書き出してください。
        </div>
        <div className="row">
          <button
            className="btn secondary"
            onClick={() =>
              withBusy('export', async () => {
                const backup = await buildBackup();
                downloadJson(backupFilename(), backup);
                toast('バックアップを書き出しました');
              })
            }
          >
            JSONで書き出す
          </button>
        </div>

        <div style={{ marginTop: 14 }}>
          <div className="row" style={{ marginBottom: 8 }}>
            <label className="check">
              <input
                type="radio"
                name="restore-mode"
                checked={restoreMode === 'merge'}
                onChange={() => setRestoreMode('merge')}
              />
              追加（マージ）
            </label>
            <label className="check">
              <input
                type="radio"
                name="restore-mode"
                checked={restoreMode === 'replace'}
                onChange={() => setRestoreMode('replace')}
              />
              全置換（既存を消す）
            </label>
          </div>
          <input
            type="file"
            accept="application/json,.json"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              void withBusy('import', async () => {
                if (restoreMode === 'replace' && !confirm('既存のデータをすべて消して置き換えます。よろしいですか？')) {
                  return;
                }
                const backup = validateBackup(JSON.parse(await f.text()));
                await restoreBackup(backup, restoreMode);
                await reload();
                toast(`${backup.candidates.length} 件を復元しました`);
              });
            }}
          />
        </div>
      </div>

      {/* ---- リセット ---- */}
      <div className="card">
        <h3>設定を初期化</h3>
        <div className="note" style={{ marginBottom: 10 }}>
          料率・送料・スコア設定を config の雛形に戻します（候補データは消えません）。
        </div>
        <button
          className="btn danger"
          onClick={() => {
            if (confirm('設定を初期値に戻します。よろしいですか？')) {
              void resetSettings().then(() => toast('設定を初期化しました'));
            }
          }}
        >
          設定を初期値に戻す
        </button>
      </div>

      <div className="card">
        <h3>データ源についての前提</h3>
        <div className="note">
          ・eBayの実売データは Terapeak（Seller Hub → Product Research）から CSV を書き出して取り込みます。
          <br />
          ・Browse API が返すのは「出品中」のみで、売れた実績ではありません。競合数と相場帯の把握に使います。
          <br />
          ・eBayの売却済みページ、メルカリ、ヤフオクの自動取得は行いません（規約違反のため）。手動で貼り付けてください。
          <br />
          ・料率・送料・為替は変動します。数字は参考値であり、最終判断は必ず自分で行ってください。
        </div>
      </div>
    </>
  );
}

function ShippingSummary({ table }: { table: ShippingTable }) {
  return (
    <div className="note" style={{ marginBottom: 10 }}>
      {Object.entries(table.methods).map(([key, m]) => (
        <div key={key}>
          {m.label}：{Object.keys(m.zones).join(' / ')}（
          {Object.values(m.zones).reduce((a, b) => a + b.length, 0)} 帯）
        </div>
      ))}
    </div>
  );
}

/** 構造が深い設定はJSONで直接編集させる（保存時に検証） */
function JsonEditor({
  label,
  value,
  onSave,
}: {
  label: string;
  value: unknown;
  onSave: (parsed: unknown) => void;
}) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState(() => JSON.stringify(value, null, 2));
  const [err, setErr] = useState<string | null>(null);

  return (
    <div style={{ marginTop: 12 }}>
      <button
        className="link"
        onClick={() => {
          if (!open) setText(JSON.stringify(value, null, 2));
          setOpen((v) => !v);
          setErr(null);
        }}
      >
        {open ? '閉じる' : `${label} を編集`}
      </button>
      {open ? (
        <>
          <textarea
            rows={12}
            value={text}
            onChange={(e) => setText(e.target.value)}
            style={{ fontFamily: 'ui-monospace, monospace', fontSize: 13, marginTop: 6 }}
            spellCheck={false}
          />
          {err ? <div className="alert error" style={{ marginTop: 8 }}>{err}</div> : null}
          <button
            className="btn secondary"
            style={{ marginTop: 8 }}
            onClick={() => {
              try {
                onSave(JSON.parse(text));
                setErr(null);
                setOpen(false);
              } catch (e) {
                setErr((e as Error).message);
              }
            }}
          >
            保存
          </button>
        </>
      ) : null}
    </div>
  );
}
