import * as THREE from 'three';
import { GRAVITY } from '../core/config';
import { VoxelBody } from '../physics/VoxelBody';
import type { World } from '../world/World';

/**
 * ワールドに存在する物体の基底。
 *
 * 当たり判定・重力・段差登りは VoxelBody をそのまま使う。プレイヤーと**同じ実装**で、
 * 動物用に別の物理は書かない。高さはスクリプトで動かさず、重力と衝突に任せる。
 */
export abstract class Entity extends VoxelBody {
  /** 見た目。EntityManager がシーンに出し入れする。 */
  readonly group = new THREE.Group();

  /** true になったら EntityManager が片付ける。 */
  removed = false;

  constructor(world: World, width: number, height: number, depth: number) {
    super(world, width, height, depth);
  }

  /** 派生クラスが水平速度を決める。ここが呼ばれた直後に物理が回る。 */
  protected abstract think(dt: number): void;

  update(dt: number): void {
    this.think(dt);

    this.velocity.y += GRAVITY * dt;

    this.moveHorizontal('x', this.velocity.x * dt, true);
    this.moveVertical(this.velocity.y * dt);
    this.moveHorizontal('z', this.velocity.z * dt, true);

    this.group.position.copy(this.position);
  }
}
