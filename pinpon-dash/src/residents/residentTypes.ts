/**
 * 住民の種類（指示書 §8）。
 *
 * ここの数値がリスクとリターンの釣り合いを決める。目安として:
 *
 *   プレイヤーの歩き 3.6 / ダッシュ 6.6（config.ts）
 *
 * 追跡速度をプレイヤーのダッシュより速くしないこと。速くすると
 * 「見つかった時点で終わり」になり、視線を切って逃げる遊びが消える。
 * 逆に歩きより遅くすると、そもそも逃げる必要がなくなる。
 *
 * 視認ゲージは gaugeUp の逆数がおよその猶予秒数だが、距離でも変わる
 * （config.ts の WATCH_RATE_NEAR / WATCH_RATE_FAR）。目安は
 *
 *   ふつう  … 目の前で約3秒、視界のふちなら約9秒
 *   おこり  … 目の前で約1.6秒
 *   ヤバい  … 目の前で約1秒
 *
 * 見つかってから角を曲がるまでの猶予がここで決まる。短くしすぎると
 * 「見つかった＝終わり」になって、逃走という遊びそのものが消える。
 */

export type ResidentKey = 'normal' | 'angry' | 'dangerous';

export interface ResidentType {
  readonly key: ResidentKey;
  readonly name: string;

  /** 警戒中の歩く速さと、追跡中の走る速さ。 */
  readonly walkSpeed: number;
  readonly chaseSpeed: number;

  /** 視野の距離と広さ（度）。広いほど物陰に入らないと見つかる。 */
  readonly viewRange: number;
  readonly viewAngle: number;

  /** 視認ゲージの増減（/秒）。 */
  readonly gaugeUp: number;
  readonly gaugeDown: number;

  /** 家の前で様子を見ている時間。ここで何も無ければ帰る。 */
  readonly suspiciousTime: number;

  /**
   * chaseStamina … 追いかけ続けられる合計時間。見えていても、これを使い切ったら
   *                息が上がって諦める。「通常の住民は短時間だけ追跡」（指示書 §8）を
   *                成立させているのはこの値で、逃げ切れるかどうかを直接決める
   * chaseTime    … 見失ってから、なお追い続ける時間。見えている間は減らない
   *                （目の前にいるのに諦める、という妙な動きを避けるため）
   * searchTime   … 最後に見た場所の周りを捜し回る時間
   */
  readonly chaseStamina: number;
  readonly chaseTime: number;
  readonly searchTime: number;

  /**
   * 諦めたあと、家に帰らずに街を歩き回る時間（追加仕様 §5〜§7）。
   *
   * これがこのゲームの後半を作る。長くするほど街に住民が溜まり、
   * 家から家への移動そのものが危険になる。0 にすると、逃げ切った時点で
   * 相手が消える昔の仕様に戻る。
   */
  readonly patrolTime: number;

  /** 徘徊中の歩く速さ。警戒中よりゆっくり歩かせると、街に馴染んで見える。 */
  readonly patrolSpeed: number;

  /** まいたときのボーナス倍率（ESCAPE_BONUS_BASE に掛ける）。 */
  readonly escapeMultiplier: number;

  /** 当たり判定の半径。 */
  readonly radius: number;

  /** 出てきたときのひとこと（コミカルな演出用）。 */
  readonly shout: string;

  readonly colors: {
    readonly skin: number;
    readonly shirt: number;
    readonly pants: number;
    readonly hair: number;
  };

  /** 見た目の特徴。危険な住民ほど分かりやすく異形にする。 */
  readonly look: {
    /** 頭の大きさの倍率。 */
    readonly headScale: number;
    /** 眉の角度（度）。大きいほど吊り上がる。 */
    readonly browAngle: number;
    /** 身長の倍率。 */
    readonly heightScale: number;
  };
}

export const RESIDENT_TYPES: Readonly<Record<ResidentKey, ResidentType>> = {
  // ふつうの住民。出てくるだけで、たいして追ってこない。
  normal: {
    key: 'normal',
    name: 'ふつうの住民',
    walkSpeed: 1.7,
    chaseSpeed: 3.0,
    viewRange: 12,
    viewAngle: 80,
    gaugeUp: 0.22,
    gaugeDown: 0.55,
    suspiciousTime: 4,
    chaseStamina: 5,
    chaseTime: 4,
    searchTime: 3,
    patrolTime: 30,
    patrolSpeed: 1.4,
    escapeMultiplier: 1,
    radius: 0.35,
    shout: 'はて…？',
    colors: { skin: 0xf0c9a4, shirt: 0x6fa8d0, pants: 0x4a5568, hair: 0x3a2f2a },
    look: { headScale: 1, browAngle: 0, heightScale: 1 },
  },

  // 怒りっぽい住民。ちゃんと追ってくるが、そのうち諦める。
  angry: {
    key: 'angry',
    name: 'おこりんぼ',
    walkSpeed: 2.1,
    chaseSpeed: 4.4,
    viewRange: 16,
    viewAngle: 100,
    gaugeUp: 0.38,
    gaugeDown: 0.4,
    suspiciousTime: 6,
    chaseStamina: 13,
    chaseTime: 9,
    searchTime: 6,
    patrolTime: 55,
    patrolSpeed: 1.7,
    escapeMultiplier: 2,
    radius: 0.38,
    shout: 'こら待てーっ！',
    colors: { skin: 0xf2b48c, shirt: 0xd9584a, pants: 0x3d4450, hair: 0x241c18 },
    look: { headScale: 1.12, browAngle: 22, heightScale: 1.04 },
  },

  // 危険な住民。視野が広く、長く追い、見失っても粘って捜す。
  dangerous: {
    key: 'dangerous',
    name: 'ヤバいひと',
    walkSpeed: 2.5,
    chaseSpeed: 5.7,
    viewRange: 22,
    viewAngle: 130,
    gaugeUp: 0.6,
    gaugeDown: 0.22,
    suspiciousTime: 8,
    chaseStamina: 28,
    chaseTime: 16,
    searchTime: 10,
    patrolTime: 90,
    patrolSpeed: 2.0,
    escapeMultiplier: 4,
    radius: 0.42,
    shout: 'みつけたぞぉ',
    colors: { skin: 0xe8a882, shirt: 0x2c2f38, pants: 0x1e2128, hair: 0x14100e },
    look: { headScale: 1.28, browAngle: 34, heightScale: 1.14 },
  },
};

/** 重み付きで種類を1つ選ぶ。重み 0 の種類は選ばれない。 */
export function pickResidentType(weights: Record<ResidentKey, number>): ResidentType {
  const keys = Object.keys(weights) as ResidentKey[];
  const total = keys.reduce((sum, key) => sum + weights[key], 0);
  if (total <= 0) return RESIDENT_TYPES.normal;

  let roll = Math.random() * total;
  for (const key of keys) {
    roll -= weights[key];
    if (roll <= 0) return RESIDENT_TYPES[key];
  }
  return RESIDENT_TYPES[keys[keys.length - 1]];
}
