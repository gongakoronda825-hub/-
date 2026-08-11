import * as THREE from 'three';
import {
  COLLISION_EPSILON,
  FLY_MOVE_SPEED,
  FLY_VERTICAL_SPEED,
  GRAVITY,
  JUMP_SPEED,
  MOVE_SPEED,
  PLAYER_DEPTH,
  PLAYER_HEIGHT,
  PLAYER_WIDTH,
  SPAWN,
  STEP_HEIGHT,
} from '../core/config';
import type { World } from '../world/World';

const HALF_W = PLAYER_WIDTH / 2;
const HALF_D = PLAYER_DEPTH / 2;

/** ソリッドなセルのブロック座標。 */
type Cell = [number, number, number];

/**
 * プレイヤー。AABB として扱い、重力と衝突解決を持つ。
 *
 * `position` は「足元の中心」。AABB は
 *   x: [x - W/2, x + W/2] / y: [y, y + H] / z: [z - D/2, z + D/2]
 *
 * 衝突は計画書 §3.3 のとおり X → Y → Z と軸ごとに分離して解決する。
 * まとめて解くと角で引っかかったり、壁沿いに動けなくなる。
 */
export class Player {
  readonly position = new THREE.Vector3(SPAWN.x, SPAWN.y, SPAWN.z);
  readonly velocity = new THREE.Vector3();
  onGround = false;

  /** 飛行中は重力が効かず、上下は verticalInput で操作する。 */
  flying = false;

  /** 飛行中の上下入力。+1 が上昇、-1 が下降、0 でその高さに留まる。 */
  verticalInput = 0;

  constructor(private readonly world: World) {}

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

    this.moveHorizontal('x', this.velocity.x * dt);
    this.moveVertical(this.velocity.y * dt);
    this.moveHorizontal('z', this.velocity.z * dt);
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
    // 飛び始めた瞬間は宙に浮くので、接地はいったん外す
    if (flying) this.onGround = false;
  }

  /** 指定セルにブロックを置いたらプレイヤーと重なるか（設置の可否判定）。 */
  intersectsBlock(bx: number, by: number, bz: number): boolean {
    const p = this.position;
    return (
      bx + 1 > p.x - HALF_W &&
      bx < p.x + HALF_W &&
      by + 1 > p.y &&
      by < p.y + PLAYER_HEIGHT &&
      bz + 1 > p.z - HALF_D &&
      bz < p.z + HALF_D
    );
  }

  private moveVertical(delta: number): void {
    if (delta === 0) return;
    this.position.y += delta;

    const cells = this.overlappingCells();
    if (cells.length === 0) {
      this.onGround = false;
      return;
    }

    if (delta > 0) {
      // 天井にぶつかった。最も低いセルの下面まで戻す。
      const ceiling = Math.min(...cells.map((c) => c[1]));
      this.position.y = ceiling - PLAYER_HEIGHT - COLLISION_EPSILON;
      this.onGround = false;
    } else {
      // 着地。最も高いセルの上面に乗せる。
      const floor = Math.max(...cells.map((c) => c[1]));
      this.position.y = floor + 1 + COLLISION_EPSILON;
      this.onGround = true;
    }
    this.velocity.y = 0;
  }

  private moveHorizontal(axis: 'x' | 'z', delta: number): void {
    if (delta === 0) return;
    this.position[axis] += delta;

    const cells = this.overlappingCells();
    if (cells.length === 0) return;

    // 進行方向に対していちばん手前のセルで止める。
    // 幅0.6のAABBは2列にまたがれるので、最小/最大を取らないと押し戻しすぎる。
    const index = axis === 'x' ? 0 : 2;
    const half = axis === 'x' ? HALF_W : HALF_D;
    const face = delta > 0
      ? Math.min(...cells.map((c) => c[index]))
      : Math.max(...cells.map((c) => c[index]));

    const stopped = delta > 0
      ? face - half - COLLISION_EPSILON
      : face + 1 + half + COLLISION_EPSILON;

    const beforeStop = this.position[axis];
    this.position[axis] = stopped;

    // 1ブロックぶんの段差は歩いたまま登る。飛行中は▲で越えればよいので効かせない。
    if (this.onGround && !this.flying) this.tryStepUp(axis, beforeStop);
  }

  /** 段差の自動昇り。上に隙間があるときだけ持ち上げる。 */
  private tryStepUp(axis: 'x' | 'z', desired: number): void {
    const savedY = this.position.y;
    const savedAxis = this.position[axis];

    this.position.y += STEP_HEIGHT;
    this.position[axis] = desired;

    if (this.overlappingCells().length > 0) {
      // 登った先も埋まっている。壁なので素直に止まる。
      this.position.y = savedY;
      this.position[axis] = savedAxis;
      return;
    }

    // 登れた。次フレームの重力で段の上に着地する。
    this.onGround = false;
  }

  /** 現在の AABB と重なっているソリッドなセル。 */
  private overlappingCells(): Cell[] {
    const p = this.position;
    const minX = Math.floor(p.x - HALF_W + COLLISION_EPSILON);
    const maxX = Math.floor(p.x + HALF_W - COLLISION_EPSILON);
    const minY = Math.floor(p.y + COLLISION_EPSILON);
    const maxY = Math.floor(p.y + PLAYER_HEIGHT - COLLISION_EPSILON);
    const minZ = Math.floor(p.z - HALF_D + COLLISION_EPSILON);
    const maxZ = Math.floor(p.z + HALF_D - COLLISION_EPSILON);

    const cells: Cell[] = [];
    for (let x = minX; x <= maxX; x++) {
      for (let y = minY; y <= maxY; y++) {
        for (let z = minZ; z <= maxZ; z++) {
          if (this.world.isSolid(x, y, z)) cells.push([x, y, z]);
        }
      }
    }
    return cells;
  }
}
