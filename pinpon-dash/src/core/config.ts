/**
 * ゲームバランスに関わる数値は、すべてこのファイルに集めてある。
 *
 * 指示書 §18 のとおり、初期値は「とりあえず遊べる」ための仮設定。
 * 実機で触りながらここだけを書き換えて調整する想定なので、
 * 他のファイルに生の数値を書き足さないこと。
 *
 * 長さの単位はメートル、時間は秒。
 */

// ── プレイヤー ───────────────────────────────────

/** プレイヤーの当たり判定は円柱ではなく円（XZ平面）。その半径。 */
export const PLAYER_RADIUS = 0.34;

/** 足元からの目線の高さ。カメラをここに置く。 */
export const EYE_HEIGHT = 1.55;

/** 歩き / ダッシュの速度。差が小さいとダッシュの意味が薄れる。 */
export const WALK_SPEED = 3.6;
export const DASH_SPEED = 6.6;

/** 目標速度への追従の速さ。大きいほどキビキビ、小さいほどヌルッと動く。 */
export const ACCELERATION = 26;

/** 走っているときの上下の揺れ（頭のブレ）。0 にすれば止まる。 */
export const BOB_AMPLITUDE = 0.055;
export const BOB_FREQUENCY = 1.7;

// ── スタミナ ─────────────────────────────────────

export const STAMINA_MAX = 100;

/** ダッシュ中の消費（/秒）。100 / 24 ≒ 4.2秒 走り続けられる。 */
export const STAMINA_DRAIN = 24;

/** 回復（/秒）。消費より遅くして、走りっぱなしにできないようにする。 */
export const STAMINA_RECOVER = 16;

/** ダッシュをやめてから回復が始まるまでの待ち時間。 */
export const STAMINA_RECOVER_DELAY = 0.7;

/**
 * 空になった後、ここまで戻らないと再ダッシュできない。
 * 0 にすると 1フレームだけ走ってはすぐ切れる、を繰り返せてしまう。
 */
export const STAMINA_DASH_MIN = 15;

// ── カメラ・操作 ─────────────────────────────────

/** pitch のクランプ（ラジアン）。真上・真下でひっくり返らないよう 85° で止める。 */
export const PITCH_LIMIT = (85 * Math.PI) / 180;

/** 視点操作の感度（ラジアン / CSSピクセル）。 */
export const LOOK_SENSITIVITY = 0.0045;

/** 1フレームのデルタタイム上限。タブ復帰時に大きく飛んで壁をすり抜けるのを防ぐ。 */
export const MAX_DELTA = 0.05;

/** 視野角（度）。ダッシュ中は少し広げてスピード感を出す。 */
export const FOV = 72;
export const FOV_DASH = 80;

// ── ピンポン ─────────────────────────────────────

/** インターホンに反応する距離。これ以内ならピンポンボタンが出る。 */
export const DOORBELL_RANGE = 3.0;

/**
 * インターホンの方を向いていないと押せない角度（度）。
 * 広くすると「気づいたら押せる」、狭くすると「狙って押す」ゲームになる。
 */
export const DOORBELL_FACING = 120;

/** 同じインターホンを連打できる間隔。0 にすると1フレーム連打で稼げてしまう。 */
export const DOORBELL_COOLDOWN = 0.45;

/** 住民がすでに出ている家をもう一度鳴らしたときの、危険度の倍率。 */
export const SAME_HOUSE_DANGER_MULTIPLIER = 1.8;

// ── 危険度 ───────────────────────────────────────

/** 危険度の上限。UI のメーターもこの値を 100% とする。 */
export const DANGER_MAX = 100;

/** ピンポン1回で上がる危険度。 */
export const DANGER_PER_PING = 9;

/** 危険度が自然に下がる速さ（/秒）と、最後のピンポンからの猶予。 */
export const DANGER_DECAY = 1.6;
export const DANGER_DECAY_DELAY = 4;

/** 追われている間は危険度を下げない（逃げ切ってから下がりはじめる）。 */
export const DANGER_FREEZE_WHILE_CHASED = true;

/**
 * 危険度の段階表。上から順に「この危険度以上ならこの段」。
 *
 * points      : 1回のピンポンで入るポイント
 * spawnChance : そのピンポンで住民が出てくる確率（0〜1）
 * weights     : 出てくる住民の種類の重み（residentTypes.ts のキー）
 * extra       : 同時に別の家からも出てくる確率（近所が騒ぎ出す）
 *
 * 段を増やしたい / 減らしたいときは、この配列に足し引きするだけでよい。
 */
export interface DangerTier {
  readonly from: number;
  readonly label: string;
  readonly points: number;
  readonly spawnChance: number;
  readonly weights: { normal: number; angry: number; dangerous: number };
  readonly extra: number;
}

export const DANGER_TIERS: readonly DangerTier[] = [
  {
    from: 0,
    label: 'しずか',
    points: 10,
    spawnChance: 0.2,
    weights: { normal: 1, angry: 0, dangerous: 0 },
    extra: 0,
  },
  {
    from: 20,
    label: 'ざわつき',
    points: 25,
    spawnChance: 0.4,
    weights: { normal: 3, angry: 2, dangerous: 0 },
    extra: 0,
  },
  {
    from: 45,
    label: 'けはい',
    points: 60,
    spawnChance: 0.62,
    weights: { normal: 2, angry: 3, dangerous: 1 },
    extra: 0.15,
  },
  {
    from: 70,
    label: 'げきおこ',
    points: 140,
    spawnChance: 0.85,
    weights: { normal: 1, angry: 3, dangerous: 3 },
    extra: 0.35,
  },
  {
    from: 90,
    label: 'まちぐるみ',
    points: 300,
    spawnChance: 1,
    weights: { normal: 0, angry: 2, dangerous: 5 },
    extra: 0.6,
  },
];

// ── 住民 ─────────────────────────────────────────

/** 同時に外に出ていられる住民の上限。増やすと重くなるので控えめに。 */
export const RESIDENT_CAP = 7;

/** ピンポンしてから玄関が開くまでの間（この間は姿が見えない）。 */
export const RESIDENT_DOOR_DELAY = 0.7;

/** 追跡中の住民がこの距離まで詰めたら捕まる。 */
export const CATCH_RANGE = 1.15;

/** 視認ゲージがこの値を超えると DETECTED から CHASE に移る。 */
export const CHASE_THRESHOLD = 0.35;

/** 住民が壁を避けるときに前方を調べる距離。 */
export const AVOID_PROBE = 1.6;

/** うろつきの行き先を選び直す間隔。移動と視界の判定は毎フレーム、これだけ間引く。 */
export const WANDER_RETARGET = 2.2;

/** 見失った直後、最後に見た位置へ向かい続ける時間。 */
export const LOST_GRACE = 1.2;

// ── 視認ゲージ ───────────────────────────────────

/**
 * ゲージが 0 → 1 でゲームオーバー。上昇の速さは住民の種類ごと
 * （residentTypes.ts の gaugeUp）に持たせてあり、通常の住民でおよそ3秒。
 */
export const WATCH_GAUGE_MAX = 1;

/**
 * 距離によるゲージの溜まりやすさ。目の前と視界のふちで、これだけ差がつく。
 *
 * 両方 1.0 にすると距離に関係なく一定になるが、それだと
 * 「見つかった直後に全力で逃げる」が意味を失う（走って離れても同じ速さで
 * 溜まってしまう）。遠ければ時間が稼げる、が逃走の前提。
 */
export const WATCH_RATE_NEAR = 1.6;
export const WATCH_RATE_FAR = 0.5;

/** 視認ゲージの表示を出しはじめる値。小さすぎるとチラつく。 */
export const WATCH_SHOW_THRESHOLD = 0.04;

// ── スコア ───────────────────────────────────────

/** 追跡してきた住民をまいたときのボーナス（種類ごとの倍率は residentTypes.ts）。 */
export const ESCAPE_BONUS_BASE = 50;

/** ハイスコアの保存先（localStorage のキー）。 */
export const HIGHSCORE_KEY = 'pinpon-dash.highscore';

// ── 見た目 ───────────────────────────────────────

/** 空の色と距離フォグ。フォグは遠くの家をぼかして、狭い街を広く見せる。 */
export const SKY_COLOR = 0x9fd2ef;
export const FOG_NEAR = 55;
export const FOG_FAR = 135;

/** カメラの描画距離。 */
export const CAMERA_FAR = 300;
