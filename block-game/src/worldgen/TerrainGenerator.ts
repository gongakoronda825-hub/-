import {
  DIRT_DEPTH,
  TERRAIN_AMPLITUDE,
  TERRAIN_BASE,
  TERRAIN_OCTAVES,
  TERRAIN_SCALE,
  WORLD_HEIGHT,
  WORLD_SEED,
} from '../core/config';
import type { Chunk } from '../world/Chunk';
import { DIRT, GRASS, STONE } from '../world/blocks';
import { fbm2 } from './noise';

/**
 * ハイトマップ地形。
 *
 * 高さは `(seed, x, z)` だけで決まる純関数。チャンクをどの順で作っても、
 * 一度離れて戻ってきても、同じ地形になる。
 */
export function surfaceHeightAt(x: number, z: number): number {
  const n = fbm2(WORLD_SEED, x, z, TERRAIN_OCTAVES, TERRAIN_SCALE);
  const h = Math.round(TERRAIN_BASE + n * TERRAIN_AMPLITUDE);
  // 岩盤(0)より下と天井を超えないように
  return Math.max(1, Math.min(WORLD_HEIGHT - 12, h));
}

/**
 * チャンクを地形で埋める。層は下から 岩盤 → 石 → 土 → 草。
 */
export function generateTerrain(chunk: Chunk): void {
  const ox = chunk.originX;
  const oz = chunk.originZ;

  for (let lz = 0; lz < 16; lz++) {
    for (let lx = 0; lx < 16; lx++) {
      const height = surfaceHeightAt(ox + lx, oz + lz);

      chunk.set(lx, 0, lz, STONE); // 岩盤代わり。抜け落ちないための蓋
      for (let y = 1; y < height - DIRT_DEPTH; y++) chunk.set(lx, y, lz, STONE);
      for (let y = Math.max(1, height - DIRT_DEPTH); y < height; y++) chunk.set(lx, y, lz, DIRT);
      chunk.set(lx, height, lz, GRASS);
    }
  }
}
