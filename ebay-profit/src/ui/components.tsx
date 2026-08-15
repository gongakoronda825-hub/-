import type { ReactNode } from 'react';
import { RISK_LABELS } from '../domain/risk';
import type { RiskFlag } from '../domain/types';

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <span className="note">{hint}</span> : null}
    </label>
  );
}

/**
 * 数値入力。iPhone でテンキーが出るよう inputMode="decimal" を必ず付ける。
 * 空文字を許すため内部は文字列で持たず、空は onChange(undefined) で表現する。
 */
export function NumberInput({
  value,
  onChange,
  step,
  min,
  placeholder,
  suffix,
}: {
  value: number | undefined | null;
  onChange: (v: number | undefined) => void;
  step?: number;
  min?: number;
  placeholder?: string;
  suffix?: string;
}) {
  const input = (
    <input
      type="text"
      inputMode="decimal"
      value={value == null || Number.isNaN(value) ? '' : String(value)}
      placeholder={placeholder}
      onChange={(e) => {
        const raw = e.target.value.trim().replace(/,/g, '');
        if (raw === '') return onChange(undefined);
        const n = Number(raw);
        if (Number.isFinite(n)) {
          if (min != null && n < min) return onChange(min);
          onChange(n);
        }
      }}
      step={step}
    />
  );
  if (!suffix) return input;
  return (
    <span className="row" style={{ flexWrap: 'nowrap' }}>
      {input}
      <span className="muted small" style={{ whiteSpace: 'nowrap' }}>
        {suffix}
      </span>
    </span>
  );
}

export function ScorePill({ score }: { score: number }) {
  const color = score >= 65 ? 'var(--accent)' : score >= 40 ? 'var(--warn)' : 'var(--danger)';
  return (
    <span className="score-pill" style={{ color }}>
      {Math.round(score)}
      <span className="small muted" style={{ fontWeight: 400 }}>
        /100
      </span>
    </span>
  );
}

export function Bar({ value, max = 100 }: { value: number; max?: number }) {
  const w = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="bar">
      <i style={{ width: `${w}%` }} />
    </div>
  );
}

export function RiskBadges({ flags }: { flags: RiskFlag[] }) {
  if (flags.length === 0) return <span className="badge ok">リスク該当なし</span>;
  return (
    <>
      {flags.map((f) => (
        <span key={f} className={f === 'low_ticket' || f === 'thin_margin' ? 'badge warn' : 'badge risk'}>
          {RISK_LABELS[f] ?? f}
        </span>
      ))}
    </>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '28px 16px' }}>
      <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <div className="note">{children}</div>
    </div>
  );
}

/** 履歴のスパークライン（依存なしのインラインSVG） */
export function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const w = 300;
  const h = 48;
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const span = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / span) * (h - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const zeroY = h - ((0 - min) / span) * (h - 6) - 3;
  const last = values[values.length - 1];
  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" aria-hidden="true">
      {min < 0 && max > 0 ? (
        <line x1="0" y1={zeroY} x2={w} y2={zeroY} stroke="#2b3760" strokeWidth="1" strokeDasharray="4 4" />
      ) : null}
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={last >= 0 ? '#22c55e' : '#f87171'}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
