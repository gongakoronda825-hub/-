import {
  COMBO_BREAKS_ON_RESIDENT,
  COMBO_DANGER_GROWTH,
  COMBO_HOLD_DISTANCE,
  COMBO_HOLD_TIME,
  COMBO_POINTS,
  COMBO_POINTS_GROWTH,
  COMBO_SPAWN_BONUS,
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
 * スコア・危険度・コンボ（追加仕様 §1〜§4, §13）。
 *
 * このゲームの駆け引きは、この3つの数字の関係にある:
 *
 *   同じ家で鳴らし続ける → コンボが伸びる → 1回のポイントが跳ね上がる
 *                                      ↘ 危険度の上がり方も、住民の出やすさも上がる
 *
 * 別の家へ移ればコンボは 1 に戻る。だから「安全な家を2〜3回ずつ回る」より
 * 「1軒でどこまで粘れるか」のほうが儲かる ── そこがこのゲームの背骨。
 */
export class GameState {
  score = 0;
  pings = 0;

  /** 0〜DANGER_MAX。 */
  danger = 0;

  /** いま何連続で同じ家を鳴らしているか。0 ならコンボなし。 */
  combo = 0;

  /** コンボが乗っている家。null ならどの家にも乗っていない。 */
  comboHouseId: number | null = null;

  /** 1回のプレイで到達した最高コンボ。結果画面に出す。 */
  bestCombo = 0;

  /** 最後にピンポンしてからの経過秒数。危険度の減衰とコンボの保持に使う。 */
  private sinceLastPing = 0;

  /** いま何段目か。 */
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
   * n 回目の連続ピンポンで入る素点。表を超えたぶんは倍率で伸ばし続ける。
   * @param count 1 以上
   */
  static comboPoints(count: number): number {
    const table = COMBO_POINTS;
    if (count <= table.length) return table[count - 1];

    let points = table[table.length - 1];
    for (let i = table.length; i < count; i++) points *= COMBO_POINTS_GROWTH;
    return Math.round(points);
  }

  /** 次にこの家を鳴らしたら何ポイント入るか（UI の予告用）。 */
  nextPoints(houseId: number): number {
    const count = this.comboHouseId === houseId ? this.combo + 1 : 1;
    return Math.round(GameState.comboPoints(count) * this.tier.pointMultiplier);
  }

  /**
   * ピンポン1回分。
   *
   * @param houseId 鳴らした家
   * @returns 入ったポイントと、その時点のコンボ
   */
  ping(houseId: number): { points: number; combo: number } {
    // 別の家なら 1 から。同じ家なら伸ばす
    this.combo = this.comboHouseId === houseId ? this.combo + 1 : 1;
    this.comboHouseId = houseId;
    this.bestCombo = Math.max(this.bestCombo, this.combo);

    // 段の判定は「鳴らした時点の危険度」で行い、そのあとに危険度を上げる。
    // 先に上げると1回のピンポンで段が飛んで、鳴らした実感と数字がずれる。
    const points = Math.round(GameState.comboPoints(this.combo) * this.tier.pointMultiplier);
    this.score += points;
    this.pings += 1;

    // 粘るほど危険度の上がり方もきつくなる
    const gain = DANGER_PER_PING * (1 + (this.combo - 1) * COMBO_DANGER_GROWTH);
    this.danger = Math.min(DANGER_MAX, this.danger + gain);
    this.sinceLastPing = 0;

    return { points, combo: this.combo };
  }

  /** そのピンポンで住民が出てくる確率。コンボが伸びるほど上がる。 */
  spawnChance(): number {
    const bonus = Math.max(0, this.combo - 1) * COMBO_SPAWN_BONUS;
    return Math.min(1, this.tier.spawnChance + bonus);
  }

  /** ボーナス加点（住民をまいたときなど）。 */
  addScore(points: number): void {
    this.score += points;
  }

  /** 住民が出てきたときの通知。設定によってはここでコンボが終わる。 */
  onResidentAppeared(houseId: number): void {
    if (COMBO_BREAKS_ON_RESIDENT && this.comboHouseId === houseId) this.breakCombo();
  }

  breakCombo(): void {
    this.combo = 0;
    this.comboHouseId = null;
  }

  /**
   * 時間経過。危険度を下げ、コンボの保持を判定する。
   *
   * @param distanceToCombo コンボが乗っている家までの距離（乗っていなければ null）
   */
  update(dt: number, chased: boolean, distanceToCombo: number | null): void {
    this.sinceLastPing += dt;

    // 逃げている間もコンボは切らさない、が初期値。長く離れれば切れる（§3）
    if (this.combo > 0) {
      const tooLong = COMBO_HOLD_TIME > 0 && this.sinceLastPing > COMBO_HOLD_TIME;
      const tooFar =
        COMBO_HOLD_DISTANCE > 0 && distanceToCombo !== null && distanceToCombo > COMBO_HOLD_DISTANCE;
      if (tooLong || tooFar) this.breakCombo();
    }

    // 追われている間は下がらない。逃げ切るまで危険なままにしておく
    if (DANGER_FREEZE_WHILE_CHASED && chased) return;
    if (this.sinceLastPing < DANGER_DECAY_DELAY) return;

    this.danger = Math.max(0, this.danger - DANGER_DECAY * dt);
  }

  reset(): void {
    this.score = 0;
    this.pings = 0;
    this.danger = 0;
    this.combo = 0;
    this.comboHouseId = null;
    this.bestCombo = 0;
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
