import * as THREE from 'three';
import { COLLISION_EPSILON, STEP_HEIGHT } from '../core/config';

/** 衝突に必要な最小限のワールド。World も動物も同じ形で参照する。 */
export interface SolidLookup {
  isSolid(x: number, y: number, z: number): boolean;
}

/** ソリッドなセルのブロック座標。 */
type Cell = [number, number, number];

/**
 * AABB × ボクセルの当たり判定を持つ物体。プレイヤーも動物もこれを継承する。
 *
 * `position` は「足元の中心」。AABB は
 *   x: [x - W/2, x + W/2] / y: [y, y + H] / z: [z - D/2, z + D/2]
 *
 * 衝突は X → Y → Z と軸ごとに分離して解く。まとめて解くと角で引っかかったり、
 * 壁沿いに動けなくなる。
 */
export class VoxelBody {
  readonly position = new THREE.Vector3();
  readonly velocity = new THREE.Vector3();
  onGround = false;

  constructor(
    protected readonly world: SolidLookup,
    readonly width: number,
    readonly height: number,
    readonly depth: number,
  ) {}

  protected get halfW(): number {
    return this.width / 2;
  }

  protected get halfD(): number {
    return this.depth / 2;
  }

  /** 指定セルにブロックを置いたら、この体と重なるか。 */
  intersectsBlock(bx: number, by: number, bz: number): boolean {
    const p = this.position;
    return (
      bx + 1 > p.x - this.halfW &&
      bx < p.x + this.halfW &&
      by + 1 > p.y &&
      by < p.y + this.height &&
      bz + 1 > p.z - this.halfD &&
      bz < p.z + this.halfD
    );
  }

  /**
   * 上下に動かして衝突を解く。接地判定も兼ねる。
   * @returns 何かにぶつかったか
   */
  protected moveVertical(delta: number): boolean {
    if (delta === 0) return false;
    this.position.y += delta;

    const cells = this.overlappingCells();
    if (cells.length === 0) {
      this.onGround = false;
      return false;
    }

    if (delta > 0) {
      // 天井。最も低いセルの下面まで戻す
      const ceiling = Math.min(...cells.map((c) => c[1]));
      this.position.y = ceiling - this.height - COLLISION_EPSILON;
      this.onGround = false;
    } else {
      // 着地。最も高いセルの上面に乗せる
      const floor = Math.max(...cells.map((c) => c[1]));
      this.position.y = floor + 1 + COLLISION_EPSILON;
      this.onGround = true;
    }
    this.velocity.y = 0;
    return true;
  }

  /**
   * 水平に動かして衝突を解く。
   * @param allowStepUp 塞がれたときに1ブロックの段差を登るか
   * @returns 壁で止められたか（段差を登れた場合は false）
   */
  protected moveHorizontal(axis: 'x' | 'z', delta: number, allowStepUp: boolean): boolean {
    if (delta === 0) return false;
    this.position[axis] += delta;

    const cells = this.overlappingCells();
    if (cells.length === 0) return false;

    // 進行方向に対していちばん手前のセルで止める。
    // AABB は2列にまたがれるので、最小/最大を取らないと押し戻しすぎる。
    const index = axis === 'x' ? 0 : 2;
    const half = axis === 'x' ? this.halfW : this.halfD;
    const face =
      delta > 0
        ? Math.min(...cells.map((c) => c[index]))
        : Math.max(...cells.map((c) => c[index]));

    const desired = this.position[axis];
    this.position[axis] =
      delta > 0 ? face - half - COLLISION_EPSILON : face + 1 + half + COLLISION_EPSILON;

    if (allowStepUp && this.onGround && this.tryStepUp(axis, desired)) return false;
    return true;
  }

  /** 段差の自動昇り。上に隙間があるときだけ持ち上げる。 */
  private tryStepUp(axis: 'x' | 'z', desired: number): boolean {
    const savedY = this.position.y;
    const savedAxis = this.position[axis];

    this.position.y += STEP_HEIGHT;
    this.position[axis] = desired;

    if (this.overlappingCells().length > 0) {
      // 登った先も埋まっている。壁なので素直に止まる
      this.position.y = savedY;
      this.position[axis] = savedAxis;
      return false;
    }

    // 登れた。次フレームの重力で段の上に着地する
    this.onGround = false;
    return true;
  }

  /** 現在の AABB と重なっているソリッドなセル。 */
  protected overlappingCells(): Cell[] {
    const p = this.position;
    const minX = Math.floor(p.x - this.halfW + COLLISION_EPSILON);
    const maxX = Math.floor(p.x + this.halfW - COLLISION_EPSILON);
    const minY = Math.floor(p.y + COLLISION_EPSILON);
    const maxY = Math.floor(p.y + this.height - COLLISION_EPSILON);
    const minZ = Math.floor(p.z - this.halfD + COLLISION_EPSILON);
    const maxZ = Math.floor(p.z + this.depth / 2 - COLLISION_EPSILON);

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

  /** 目の前（進行方向）が塞がっているか。AI が方向を選び直すのに使う。 */
  protected isBlockedAhead(dx: number, dz: number, distance: number): boolean {
    const p = this.position;
    const x = p.x + dx * distance;
    const z = p.z + dz * distance;
    const minY = Math.floor(p.y + COLLISION_EPSILON);
    const maxY = Math.floor(p.y + this.height - COLLISION_EPSILON);

    for (let y = minY; y <= maxY; y++) {
      if (this.world.isSolid(Math.floor(x), y, Math.floor(z))) {
        // 1段上が空いていれば登れるので「塞がれ」とはみなさない
        if (y === minY && !this.world.isSolid(Math.floor(x), y + 1, Math.floor(z))) continue;
        return true;
      }
    }
    return false;
  }
}
