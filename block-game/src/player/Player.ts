import type * as THREE from 'three';
import {
  FLY_MOVE_SPEED,
  FLY_VERTICAL_SPEED,
  GRAVITY,
  JUMP_SPEED,
  MOVE_SPEED,
  PLAYER_DEPTH,
  PLAYER_HEIGHT,
  PLAYER_WIDTH,
} from '../core/config';
import { VoxelBody } from '../physics/VoxelBody';
import type { World } from '../world/World';

/**
 * プレイヤー。当たり判定・重力・段差登りは VoxelBody（動物と共有）に任せ、
 * ここは入力の解釈と飛行だけを持つ。
 */
export class Player extends VoxelBody {
  /** 飛行中は重力が効かず、上下は verticalInput で操作する。 */
  flying = false;

  /** 飛行中の上下入力。+1 が上昇、-1 が下降、0 でその高さに留まる。 */
  verticalInput = 0;

  constructor(world: World) {
    super(world, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_DEPTH);
  }

  /**
   * @param dt デルタタイム（秒）
   * @param move 水平方向の移動入力。長さ 0〜1 のワールド方向ベクトル
   */
  update(dt: number, move: THREE.Vector3): void {
    const speed = this.flying ? FLY_MOVE_SPEED : MOVE_SPEED;
    this.velocity.x = move.x * speed;
    this.velocity.z = move.z * speed;

    if (this.flying) {
      // 重力の代わりに上下入力をそのまま速度にする（慣性なしのホバー）
      this.velocity.y = this.verticalInput * FLY_VERTICAL_SPEED;
    } else {
      this.velocity.y += GRAVITY * dt;
    }

    // 段差の自動昇りは歩いているときだけ。飛行中は▲で越えればよい
    const step = !this.flying;
    this.moveHorizontal('x', this.velocity.x * dt, step);
    this.moveVertical(this.velocity.y * dt);
    this.moveHorizontal('z', this.velocity.z * dt, step);
  }

  /** ジャンプ。接地しているときだけ跳べる（空中で二段ジャンプはしない）。 */
  jump(): void {
    if (this.flying || !this.onGround) return;
    this.velocity.y = JUMP_SPEED;
    this.onGround = false;
  }

  /** 飛行の切り替え。入りも抜けも速度をリセットする。 */
  setFlying(flying: boolean): void {
    this.flying = flying;
    this.velocity.y = 0;
    this.verticalInput = 0;
    if (flying) this.onGround = false;
  }

  /** 指定の水平位置の地面に立たせる。 */
  placeOnGround(x: number, z: number, y: number): void {
    this.position.set(x, y, z);
    this.velocity.set(0, 0, 0);
    this.onGround = true;
  }
}
