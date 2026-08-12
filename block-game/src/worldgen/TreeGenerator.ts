import {
  CHUNK_SIZE,
  TREE_DENSITY,
  TREE_LEAF_RADIUS,
  TREE_SPACING,
  TREE_TRUNK_MAX,
  TREE_TRUNK_MIN,
  WORLD_SEED,
} from '../core/config';
import type { Chunk } from '../world/Chunk';
import { AIR, LEAVES, WOOD } from '../world/blocks';
import { hash2, hash3 } from './noise';
import { surfaceHeightAt } from './TerrainGenerator';

const TREE_SEED = WORLD_SEED ^ 0x5eed7ee;

/** 木が水平方向にはみ出す最大距離。 */
const OVERHANG = TREE_LEAF_RADIUS;

/**
 * その列に木が生えるか。生えるなら幹の高さを返す。
 *
 * `(seed, x, z)` の純関数。チャンクの生成順に依存しない。
 * 密集を避けるため、候補のうち「近傍で優先度が最大のもの」だけを残す
 * （距離 TREE_SPACING 以内に必ず1本だけが残る）。
 */
function trunkHeightAt(x: number, z: number): number | null {
  if (hash2(TREE_SEED, x, z) >= TREE_DENSITY) return null;

  const priority = hash3(TREE_SEED, x, z, 1);
  for (let dz = -TREE_SPACING; dz <= TREE_SPACING; dz++) {
    for (let dx = -TREE_SPACING; dx <= TREE_SPACING; dx++) {
      if (dx === 0 && dz === 0) continue;
      if (hash2(TREE_SEED, x + dx, z + dz) >= TREE_DENSITY) continue;
      if (hash3(TREE_SEED, x + dx, z + dz, 1) > priority) return null;
    }
  }

  const t = hash3(TREE_SEED, x, z, 2);
  return TREE_TRUNK_MIN + Math.floor(t * (TREE_TRUNK_MAX - TREE_TRUNK_MIN + 1));
}

/**
 * チャンクに木を書き込む。
 *
 * チャンク端の木は隣にはみ出す。保留キューで後から書き足す手もあるが、
 * ここでは **チャンクを外側に OVERHANG ぶん広げて走査し、はみ出した分を捨てる**。
 * 隣チャンクは自分の走査で同じ木を同じ形に描くので、生成順に関係なく
 * 木が欠けることも二重に生えることもない。
 */
export function generateTrees(chunk: Chunk): void {
  const ox = chunk.originX;
  const oz = chunk.originZ;

  for (let z = -OVERHANG; z < CHUNK_SIZE + OVERHANG; z++) {
    for (let x = -OVERHANG; x < CHUNK_SIZE + OVERHANG; x++) {
      const wx = ox + x;
      const wz = oz + z;

      const trunk = trunkHeightAt(wx, wz);
      if (trunk === null) continue;

      const ground = surfaceHeightAt(wx, wz);
      placeTree(chunk, ox, oz, wx, wz, ground, trunk);
    }
  }
}

function placeTree(
  chunk: Chunk,
  ox: number,
  oz: number,
  wx: number,
  wz: number,
  ground: number,
  trunk: number,
): void {
  /** ワールド座標で書く。チャンクの外なら捨てる。 */
  const put = (x: number, y: number, z: number, id: number, onlyIfAir: boolean): void => {
    const lx = x - ox;
    const lz = z - oz;
    if (lx < 0 || lx >= CHUNK_SIZE || lz < 0 || lz >= CHUNK_SIZE) return;
    if (onlyIfAir && chunk.get(lx, y, lz) !== AIR) return;
    chunk.set(lx, y, lz, id);
  };

  const top = ground + trunk;

  // 葉。上2段は細く、下2段は広く。角を落として丸みを出す
  for (let dy = -2; dy <= 1; dy++) {
    const r = dy <= -1 ? TREE_LEAF_RADIUS : 1;
    for (let dz = -r; dz <= r; dz++) {
      for (let dx = -r; dx <= r; dx++) {
        if (r > 1 && Math.abs(dx) === r && Math.abs(dz) === r) continue;
        put(wx + dx, top + dy, wz + dz, LEAVES, true);
      }
    }
  }

  // 幹。葉より後に置いて、幹が葉に食われないようにする
  for (let y = ground + 1; y <= top; y++) put(wx, y, wz, WOOD, false);
}
