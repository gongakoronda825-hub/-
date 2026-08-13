import {
  DANGER_DECAY,
  DANGER_DECAY_DELAY,
  DANGER_FREEZE_WHILE_CHASED,
  DANGER_MAX,
  DANGER_PER_PING,
  DANGER_TIERS,
  HIGHSCORE_KEY,
  type DangerTier,
} from './config';

/**
 * スコアと危険度（指示書 §6, §7）。
 *
 * このゲームの駆け引きはすべてこの2つの数字の関係にある:
 *
 *   ピンポンする → 危険度が上がる → 入るポイントが増える
 *                              ↘ 住民が出てくる確率も上がる
 *
 * 危険度は時間で下がるので、「危ないから少し休む」か「今のうちにもう1回」かを
 * プレイヤーが選べる。段の切り方と数値は config.ts の DANGER_TIERS 側にある。
 */
export class GameState {
  score = 0;
  pings = 0;

  /** 0〜DANGER_MAX。 */
  danger = 0;

  /** 最後にピンポンしてからの経過秒数。減衰の猶予に使う。 */
  private sinceLastPing = 0;

  /** いま何段目か。UI の表示に使う。 */
  get tier(): DangerTier {
    let current = DANGER_TIERS[0];
    for (const tier of DANGER_TIERS) {
      if (this.danger >= tier.from) current = tier;
    }
    return current;
  }

  /** 0〜1。メーターの表示用。 */
  get dangerRatio(): number {
    return this.danger / DANGER_MAX;
  }

  /**
   * ピンポン1回分。入ったポイントを返す。
   *
   * @param dangerMultiplier 危険度の上がり方の倍率。すでに住民が出ている家を
   *   もう一度鳴らしたときなど、呼び出し側が状況に応じて渡す。
   */
  ping(dangerMultiplier = 1): number {
    // 段の判定は「鳴らした時点の危険度」で行い、そのあとに危険度を上げる。
    // 先に上げると1回のピンポンで段が飛んで、鳴らした実感と数字がずれる。
    const points = this.tier.points;
    this.score += points;
    this.pings += 1;

    this.danger = Math.min(DANGER_MAX, this.danger + DANGER_PER_PING * dangerMultiplier);
    this.sinceLastPing = 0;

    return points;
  }

  /** ボーナス加点（住民をまいたときなど）。 */
  addScore(points: number): void {
    this.score += points;
  }

  /** 時間経過。危険度をゆっくり下げる。 */
  update(dt: number, chased: boolean): void {
    this.sinceLastPing += dt;

    // 追われている間は下がらない。逃げ切るまで危険なままにしておく
    if (DANGER_FREEZE_WHILE_CHASED && chased) return;
    if (this.sinceLastPing < DANGER_DECAY_DELAY) return;

    this.danger = Math.max(0, this.danger - DANGER_DECAY * dt);
  }

  reset(): void {
    this.score = 0;
    this.pings = 0;
    this.danger = 0;
    this.sinceLastPing = 0;
  }

  // ── ハイスコア ─────────────────────────────────

  /** localStorage が使えない環境（プライベートモードなど）では 0 のまま。 */
  static loadHighscore(): number {
    try {
      return Number(localStorage.getItem(HIGHSCORE_KEY) ?? 0) || 0;
    } catch {
      return 0;
    }
  }

  static saveHighscore(score: number): void {
    try {
      localStorage.setItem(HIGHSCORE_KEY, String(score));
    } catch {
      /* 保存できなくても遊べるので黙って続ける */
    }
  }
}
