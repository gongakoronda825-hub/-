import {
  HERD_MAX,
  HERD_MIN,
  MOB_CAP,
  SPAWN_INTERVAL,
  SPAWN_MAX_DISTANCE,
  SPAWN_MIN_DISTANCE,
  WORLD_HEIGHT,
} from '../core/config';
import { AIR, GRASS } from '../world/blocks';
import type { World } from '../world/World';
import { Animal } from './Animal';
import { randomSpecies, type AnimalSpecies } from './animals';
import type { EntityManager } from './EntityManager';

/** 1回の湧き試行で何箇所まで場所を探すか。 */
const PLACE_ATTEMPTS = 12;

/**
 * 動物の湧きと個体数管理。
 *
 * 草の地表にだけ、2〜4頭の群れで湧かせる。上限（MOB_CAP）に達したら湧かせない。
 * 保存はしない — 離れれば消え、戻ってくればまた湧く。
 */
export class SpawnManager {
  private timer = 0;

  constructor(
    private readonly world: World,
    private readonly entities: EntityManager,
  ) {}

  update(dt: number, playerX: number, playerZ: number): void {
    this.timer += dt;
    if (this.timer < SPAWN_INTERVAL) return;
    this.timer = 0;

    if (this.entities.count >= MOB_CAP) return;

    const spot = this.findSpot(playerX, playerZ);
    if (!spot) return;

    // 群れで湧かせる。上限は超えない
    const species = randomSpecies();
    const herd = HERD_MIN + Math.floor(Math.random() * (HERD_MAX - HERD_MIN + 1));
    const room = MOB_CAP - this.entities.count;

    for (let i = 0; i < Math.min(herd, room); i++) {
      // 群れは少し散らばらせる。散らした先が湧けない地面なら諦める
      const x = spot.x + (Math.random() - 0.5) * 5;
      const z = spot.z + (Math.random() - 0.5) * 5;
      const y = this.spawnableY(x, z, species);
      if (y === null) continue;

      this.entities.add(new Animal(this.world, species, x, y, z));
    }
  }

  /** プレイヤーから適度に離れた、草の地表を探す。 */
  private findSpot(playerX: number, playerZ: number): { x: number; z: number } | null {
    for (let i = 0; i < PLACE_ATTEMPTS; i++) {
      const angle = Math.random() * Math.PI * 2;
      const distance = SPAWN_MIN_DISTANCE + Math.random() * (SPAWN_MAX_DISTANCE - SPAWN_MIN_DISTANCE);
      const x = playerX + Math.cos(angle) * distance;
      const z = playerZ + Math.sin(angle) * distance;

      if (this.spawnableY(x, z, null) !== null) return { x, z };
    }
    return null;
  }

  /**
   * その位置に湧けるか。湧けるなら足元の y を返す。
   *
   * 地表が草で、その上が体の高さぶん空いていること。ブロックの中に湧かせない。
   */
  private spawnableY(x: number, z: number, species: AnimalSpecies | null): number | null {
    const bx = Math.floor(x);
    const bz = Math.floor(z);

    for (let y = WORLD_HEIGHT - 1; y >= 1; y--) {
      const here = this.world.getBlock(bx, y, bz);
      if (here === AIR) continue;

      // 最初に見つかった地面が草でなければ湧かない
      if (here !== GRASS) return null;

      // 体が入る隙間があるか（最低2ブロック）
      const need = species ? Math.ceil(species.height) : 2;
      for (let dy = 1; dy <= need; dy++) {
        if (this.world.getBlock(bx, y + dy, bz) !== AIR) return null;
      }
      return y + 1;
    }
    return null;
  }
}
