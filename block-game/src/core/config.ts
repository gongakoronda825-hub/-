/**
 * ゲーム全体の定数。実機で触りながら調整する前提の初期値。
 * 計画書 §5 の値をそのまま入れてある。
 */

/** 破壊・設置に共通のリーチ距離（ブロック単位）。Raycaster.far もこの値に揃える。 */
export const REACH = 5;

/** 重力加速度（units/s²）。 */
export const GRAVITY = -25;

/** 水平移動速度（units/s）。 */
export const MOVE_SPEED = 4;

/**
 * ジャンプの初速（units/s）。重力 -25 との組み合わせで 8²/(2×25) = 1.28 ブロック上がる。
 * 1ブロックの段差を余裕をもって越えられて、2段は登れない高さ。
 */
export const JUMP_SPEED = 8;

/** 飛行中の水平移動速度。歩きより少し速い。 */
export const FLY_MOVE_SPEED = 6;

/** 飛行中に▲▼で上下する速度（units/s）。 */
export const FLY_VERTICAL_SPEED = 5;

/** 2回連打とみなす間隔（ミリ秒）。 */
export const DOUBLE_TAP_MS = 300;

/** プレイヤーAABBのサイズ。位置は「足元の中心」で保持する。 */
export const PLAYER_WIDTH = 0.6;
export const PLAYER_HEIGHT = 1.8;
export const PLAYER_DEPTH = 0.6;

/** 足元からの目線の高さ。カメラをここに置く。 */
export const EYE_HEIGHT = 1.6;

/** pitch のクランプ（ラジアン）。真上・真下でひっくり返らないよう 89° で止める。 */
export const PITCH_LIMIT = (89 * Math.PI) / 180;

/** 視点操作の感度（ラジアン / CSSピクセル）。 */
export const LOOK_SENSITIVITY = 0.005;

/** 衝突解決で面にめり込まないための余白。 */
export const COLLISION_EPSILON = 1e-3;

/**
 * 1ブロックまでの段差を自動で登る高さ。
 * ジャンプ操作を持たないので、これが無いと足元にブロックを置いた時点で詰む。
 */
export const STEP_HEIGHT = 1.0;

/** 1フレームのデルタタイム上限（秒）。タブ復帰時に大きく飛んですり抜けるのを防ぐ。 */
export const MAX_DELTA = 0.05;

/** プレイヤーの初期位置（水平のみ。高さは地形から求める）。 */
export const SPAWN = { x: 8.5, z: 8.5 } as const;

// ── ワールド ─────────────────────────────────────

/** ワールド生成のシード。同じ値なら毎回まったく同じ地形になる。 */
export const WORLD_SEED = 20260812;

/** チャンクの水平サイズ（列数）とワールドの高さ。 */
export const CHUNK_SIZE = 16;
export const WORLD_HEIGHT = 64;

/** プレイヤーの周囲いくつのチャンクを描くか。モバイルを考えて欲張らない。 */
export const RENDER_RADIUS = 5;

/** 起動時に同期生成する半径。ここまでは「はじめる」を押した時点で出来ている。 */
export const INITIAL_RADIUS = 3;

/** 1フレームでチャンクの生成・メッシュ化に使ってよい時間（ミリ秒）。 */
export const CHUNK_BUDGET_MS = 6;

/** 距離フォグ。チャンクのポップインを隠す。 */
export const FOG_NEAR = 42;
export const FOG_FAR = 78;

// ── 地形 ────────────────────────────────────────

/** 地表の基準高さと、そこからの起伏の振幅。 */
export const TERRAIN_BASE = 30;
export const TERRAIN_AMPLITUDE = 20;

/** ノイズの基本スケール（ブロック単位。大きいほど なだらか）。 */
export const TERRAIN_SCALE = 96;

/** fBm のオクターブ数。 */
export const TERRAIN_OCTAVES = 4;

/** 表面の下、土の層の厚さ。それより下は石。 */
export const DIRT_DEPTH = 3;

// ── 木 ──────────────────────────────────────────

/** 草の地表1マスあたりに木が生える確率。 */
export const TREE_DENSITY = 0.015;

/** 木同士の最小間隔（ブロック）。 */
export const TREE_SPACING = 6;

/** 幹の高さの範囲と、葉が広がる水平半径。 */
export const TREE_TRUNK_MIN = 4;
export const TREE_TRUNK_MAX = 6;
export const TREE_LEAF_RADIUS = 2;

// ── 動物 ────────────────────────────────────────

/** 読み込み範囲内に保つ動物の上限。 */
export const MOB_CAP = 14;

/** 1つの群れの頭数。 */
export const HERD_MIN = 2;
export const HERD_MAX = 4;

/** 湧きを試みる間隔（秒）と、プレイヤーからの距離の範囲。 */
export const SPAWN_INTERVAL = 2.5;
export const SPAWN_MIN_DISTANCE = 16;
export const SPAWN_MAX_DISTANCE = 48;

/** この距離より遠い動物は消える。 */
export const DESPAWN_DISTANCE = 72;

/** 動物の歩く速さ。プレイヤーより遅い。 */
export const ANIMAL_SPEED = 1.2;

/** うろつき・立ち止まりの持続時間（秒）。 */
export const WANDER_MIN = 2;
export const WANDER_MAX = 5;
export const IDLE_MIN = 1;
export const IDLE_MAX = 3;

/** AI が次の判断をするまでの間隔（秒）。物理は毎フレーム、判断はこの間隔。 */
export const AI_TICK = 0.4;
