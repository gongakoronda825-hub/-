/**
 * データソース共通のHTTP層。
 * 外部APIは必ずサーバーレスプロキシ（/api/*）越しに叩く。ブラウザから直叩きは
 * CORS で通らないうえ、APIキーがクライアントに露出するため禁止。
 */

export class DataSourceError extends Error {
  readonly status?: number;
  readonly hint?: string;
  constructor(message: string, opts: { status?: number; hint?: string } = {}) {
    super(message);
    this.name = 'DataSourceError';
    this.status = opts.status;
    this.hint = opts.hint;
  }
}

export async function getJson<T>(
  apiBase: string,
  path: string,
  params: Record<string, string | number | undefined>,
  signal?: AbortSignal,
): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null && v !== '') qs.set(k, String(v));
  }
  const base = apiBase.replace(/\/$/, '');
  const url = `${base}/${path}${qs.toString() ? `?${qs}` : ''}`;

  let res: Response;
  try {
    res = await fetch(url, { signal, headers: { accept: 'application/json' } });
  } catch (e) {
    throw new DataSourceError('プロキシに接続できませんでした', {
      hint: 'ローカル開発中は `vercel dev` などで /api を動かすか、設定画面の APIベースURL をデプロイ先に向けてください。オフライン時は手動入力で計算できます。',
    });
  }

  if (!res.ok) {
    let detail = '';
    try {
      const body = (await res.json()) as { error?: string; hint?: string };
      detail = body?.error ?? '';
      if (body?.hint) {
        throw new DataSourceError(detail || `HTTP ${res.status}`, { status: res.status, hint: body.hint });
      }
    } catch (e) {
      if (e instanceof DataSourceError) throw e;
      // JSON以外（静的ホストの404 HTML等）はそのまま下のメッセージにする
    }
    if (res.status === 404 && !detail) {
      throw new DataSourceError(`${url} が見つかりません（サーバーレス関数が未デプロイの可能性）`, {
        status: 404,
        hint: 'このURLは /api/* のサーバーレス関数です。静的ホストのみで動かしている場合は関数が存在しません。関数をデプロイするか、設定画面の APIベースURL をデプロイ先に向けてください。手動入力だけでも着地利益の計算は使えます。',
      });
    }
    throw new DataSourceError(detail || `HTTP ${res.status}`, { status: res.status });
  }

  return (await res.json()) as T;
}
