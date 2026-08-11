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

/** プレイヤーの初期位置（足元）。 */
export const SPAWN = { x: 0.5, y: 1, z: 6.5 } as const;
