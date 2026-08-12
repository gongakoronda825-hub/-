import type * as THREE from 'three';
import { DESPAWN_DISTANCE, WORLD_HEIGHT } from '../core/config';
import type { Entity } from './Entity';

/**
 * 全エンティティの保持・更新・片付け。
 *
 * 物理は毎フレーム全員に回す（頭数は MOB_CAP で抑えてある）。
 * 遠くなった個体と、奈落へ落ちた個体はここで消す。
 */
export class EntityManager {
  private readonly entities: Entity[] = [];

  constructor(private readonly scene: THREE.Scene) {}

  get count(): number {
    return this.entities.length;
  }

  all(): readonly Entity[] {
    return this.entities;
  }

  add(entity: Entity): void {
    this.entities.push(entity);
    this.scene.add(entity.group);
  }

  update(dt: number, playerX: number, playerZ: number): void {
    for (let i = this.entities.length - 1; i >= 0; i--) {
      const entity = this.entities[i];
      entity.update(dt);

      const dx = entity.position.x - playerX;
      const dz = entity.position.z - playerZ;
      const tooFar = Math.hypot(dx, dz) > DESPAWN_DISTANCE;
      const fellOut = entity.position.y < -10 || entity.position.y > WORLD_HEIGHT + 10;

      if (entity.removed || tooFar || fellOut) {
        this.scene.remove(entity.group);
        this.entities.splice(i, 1);
      }
    }
  }

  /** いちばん近いエンティティまでの水平距離。1体もいなければ null。 */
  nearestDistance(x: number, z: number): number | null {
    let best: number | null = null;
    for (const entity of this.entities) {
      const d = Math.hypot(entity.position.x - x, entity.position.z - z);
      if (best === null || d < best) best = d;
    }
    return best;
  }

  /** 全部消す（デバッグ・再スポーン用）。 */
  clear(): void {
    for (const entity of this.entities) this.scene.remove(entity.group);
    this.entities.length = 0;
  }
}
