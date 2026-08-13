import * as THREE from 'three';
import {
  ACCELERATION,
  BOB_AMPLITUDE,
  BOB_FREQUENCY,
  DASH_SPEED,
  EYE_HEIGHT,
  PLAYER_RADIUS,
  STAMINA_DASH_MIN,
  STAMINA_DRAIN,
  STAMINA_MAX,
  STAMINA_RECOVER,
  STAMINA_RECOVER_DELAY,
  WALK_SPEED,
} from '../core/config';
import type { ColliderSet } from '../physics/Collision';

/**
 * プレイヤー。
 *
 * 街は平らなので高さの計算は無く、当たり判定は XZ 平面の円だけ（指示書 §4）。
 * ジャンプもよじ登りも持たない ── 塀を越えられないことがこのゲームの前提で、
 * 逃走は「速さ」ではなく「視線の切り方」で成立させる。
 */
export class Player {
  readonly position = new THREE.Vector3();

  /** 現在の水平速度。入力そのものではなく、加速で追従させた結果。 */
  readonly velocity = new THREE.Vector3();

  stamina = STAMINA_MAX;

  /** 実際にダッシュできているか（ボタンを押していてもスタミナが無ければ false）。 */
  dashing = false;

  /** スタミナを使い切った直後は、少し回復するまで再ダッシュできない。 */
  private exhausted = false;

  private recoverTimer = 0;
  private bobPhase = 0;

  constructor(private readonly colliders: ColliderSet) {}

  /** 目線の高さ。走っているときだけ上下に揺れる。 */
  get eyeY(): number {
    return this.position.y + EYE_HEIGHT + Math.sin(this.bobPhase) * BOB_AMPLITUDE;
  }

  /** 0〜1 のスタミナ。UI 用。 */
  get staminaRatio(): number {
    return this.stamina / STAMINA_MAX;
  }

  /** ダッシュを始められる状態か。UI のボタンの表示に使う。 */
  get canDash(): boolean {
    return !this.exhausted && this.stamina > 0;
  }

  /** 指定の位置に立たせる。スタミナと勢いもまっさらに戻す。 */
  place(x: number, z: number): void {
    this.position.set(x, 0, z);
    this.velocity.set(0, 0, 0);
    this.stamina = STAMINA_MAX;
    this.dashing = false;
    this.exhausted = false;
    this.recoverTimer = 0;
    this.bobPhase = 0;
  }

  /**
   * @param dt デルタタイム（秒）
   * @param move 水平の移動入力。長さ 0〜1 のワールド方向ベクトル
   * @param wantDash ダッシュボタンが押されているか
   */
  update(dt: number, move: THREE.Vector3, wantDash: boolean): void {
    this.updateStamina(dt, wantDash, move.lengthSq() > 0.01);

    const speed = this.dashing ? DASH_SPEED : WALK_SPEED;

    // 入力方向の速度へ、一定の割合で近づける。急発進・急停止を避けるため。
    const targetX = move.x * speed;
    const targetZ = move.z * speed;
    const follow = Math.min(dt * ACCELERATION, 1);
    this.velocity.x += (targetX - this.velocity.x) * follow;
    this.velocity.z += (targetZ - this.velocity.z) * follow;

    const nextX = this.position.x + this.velocity.x * dt;
    const nextZ = this.position.z + this.velocity.z * dt;

    // 動かしてから押し出す。軸ごとに解くより、壁ぎわを滑らせるのが素直。
    const resolved = this.colliders.resolveCircle(nextX, nextZ, PLAYER_RADIUS);
    this.position.x = resolved.x;
    this.position.z = resolved.z;

    const actualSpeed = Math.hypot(this.velocity.x, this.velocity.z);
    this.bobPhase += dt * actualSpeed * BOB_FREQUENCY;
  }

  private updateStamina(dt: number, wantDash: boolean, moving: boolean): void {
    this.dashing = wantDash && moving && this.canDash;

    if (this.dashing) {
      this.stamina = Math.max(0, this.stamina - STAMINA_DRAIN * dt);
      this.recoverTimer = STAMINA_RECOVER_DELAY;
      if (this.stamina === 0) {
        this.exhausted = true;
        this.dashing = false;
      }
      return;
    }

    // ボタンを離してすぐには回復しない。連打で走り続けられないようにするため。
    if (this.recoverTimer > 0) {
      this.recoverTimer -= dt;
      return;
    }

    this.stamina = Math.min(STAMINA_MAX, this.stamina + STAMINA_RECOVER * dt);
    if (this.exhausted && this.stamina >= STAMINA_DASH_MIN) this.exhausted = false;
  }
}
