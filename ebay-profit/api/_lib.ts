/**
 * サーバーレス関数の共通ヘルパ。
 * APIキーは必ずここ（サーバー側の環境変数）だけで扱い、クライアントへ返さない。
 */

export type Req = { method?: string; query?: Record<string, string | string[] | undefined>; url?: string };
export type Res = {
  status: (code: number) => Res;
  json: (body: unknown) => void;
  setHeader: (name: string, value: string) => void;
};

export function param(req: Req, name: string): string | undefined {
  const v = req.query?.[name];
  if (Array.isArray(v)) return v[0];
  return v ?? undefined;
}

export function fail(res: Res, status: number, error: string, hint?: string): void {
  res.status(status).json({ error, ...(hint ? { hint } : {}) });
}

export function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) {
    throw new MissingEnvError(name);
  }
  return v;
}

export class MissingEnvError extends Error {
  readonly envName: string;
  constructor(envName: string) {
    super(`環境変数 ${envName} が未設定です`);
    this.name = 'MissingEnvError';
    this.envName = envName;
  }
}

export function handleError(res: Res, e: unknown): void {
  if (e instanceof MissingEnvError) {
    fail(
      res,
      501,
      e.message,
      `ホスティング先のプロジェクト設定で環境変数 ${e.envName} を追加し、再デプロイしてください。キーはサーバー側だけに置きます。`,
    );
    return;
  }
  const msg = e instanceof Error ? e.message : String(e);
  fail(res, 502, `外部APIの呼び出しに失敗しました: ${msg}`);
}

/** 短時間の CDN キャッシュ。同じ検索の連打で外部APIのクォータを焼かないため。 */
export function cache(res: Res, seconds: number): void {
  res.setHeader('cache-control', `public, max-age=0, s-maxage=${seconds}, stale-while-revalidate=${seconds * 4}`);
}

export function percentile(sortedAsc: number[], p: number): number | undefined {
  if (sortedAsc.length === 0) return undefined;
  if (sortedAsc.length === 1) return sortedAsc[0];
  const idx = (sortedAsc.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sortedAsc[lo];
  return sortedAsc[lo] + (sortedAsc[hi] - sortedAsc[lo]) * (idx - lo);
}
