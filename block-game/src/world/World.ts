import * as THREE from 'three';
import { CHUNK_SIZE, WORLD_HEIGHT } from '../core/config';
import { generateTerrain } from '../worldgen/TerrainGenerator';
import { generateTrees } from '../worldgen/TreeGenerator';
import { Chunk, chunkKey, toChunkCoord } from './Chunk';
import { AIR, GRASS, type BlockId, isSolid as blockIsSolid } from './blocks';

/**
 * チャンクの集合を束ねる窓口。
 *
 * ワールド座標での読み書きだけを外に見せ、チャンクの分割は中に隠す。
 * プレイヤーも動物もレイキャストも、ここだけを見ればよい。
 */
export class World {
  readonly chunks = new Map<string, Chunk>();

  /** プレイヤーが壊した/置いた回数。デバッグ表示に出す。 */
  edits = 0;

  constructor(readonly scene: THREE.Scene) {}

  chunkAt(cx: number, cz: number): Chunk | undefined {
    return this.chunks.get(chunkKey(cx, cz));
  }

  /** まだ無ければ作る。データは空のまま（生成は ChunkManager が行う）。 */
  ensureChunk(cx: number, cz: number): Chunk {
    const key = chunkKey(cx, cz);
    let chunk = this.chunks.get(key);
    if (!chunk) {
      chunk = new Chunk(cx, cz);
      this.chunks.set(key, chunk);
    }
    return chunk;
  }

  /** 地形と木を書き込む。ここまでは隣チャンクを一切参照しない。 */
  generate(chunk: Chunk): void {
    if (chunk.generated) return;
    generateTerrain(chunk);
    generateTrees(chunk);
    chunk.generated = true;
    chunk.dirty = true;
  }

  /** 未生成のチャンクや範囲外は空気。 */
  getBlock(x: number, y: number, z: number): BlockId {
    if (y < 0 || y >= WORLD_HEIGHT) return AIR;
    const chunk = this.chunkAt(toChunkCoord(x), toChunkCoord(z));
    if (!chunk || !chunk.generated) return AIR;
    return chunk.get(x - chunk.originX, y, z - chunk.originZ);
  }

  isSolid(x: number, y: number, z: number): boolean {
    return blockIsSolid(this.getBlock(Math.floor(x), Math.floor(y), Math.floor(z)));
  }

  /**
   * ブロックを書き換える。チャンクを dirty にし、端なら隣も dirty にする
   * （隣の面カリング結果が変わるので、再メッシュしないと穴が残る）。
   */
  setBlock(x: number, y: number, z: number, id: BlockId): boolean {
    if (y < 0 || y >= WORLD_HEIGHT) return false;

    const cx = toChunkCoord(x);
    const cz = toChunkCoord(z);
    const chunk = this.chunkAt(cx, cz);
    if (!chunk || !chunk.generated) return false;

    const lx = x - chunk.originX;
    const lz = z - chunk.originZ;
    if (chunk.get(lx, y, lz) === id) return false;

    chunk.set(lx, y, lz, id);
    chunk.dirty = true;

    if (lx === 0) this.markDirty(cx - 1, cz);
    if (lx === CHUNK_SIZE - 1) this.markDirty(cx + 1, cz);
    if (lz === 0) this.markDirty(cx, cz - 1);
    if (lz === CHUNK_SIZE - 1) this.markDirty(cx, cz + 1);

    return true;
  }

  private markDirty(cx: number, cz: number): void {
    const chunk = this.chunkAt(cx, cz);
    if (chunk?.generated) chunk.dirty = true;
  }

  /**
   * その列で立てる高さ（足元の y）。生成済みチャンクの実データから探す。
   * 見つからなければ null。
   */
  standingHeight(x: number, z: number): number | null {
    const bx = Math.floor(x);
    const bz = Math.floor(z);
    const chunk = this.chunkAt(toChunkCoord(bx), toChunkCoord(bz));
    if (!chunk || !chunk.generated) return null;

    for (let y = WORLD_HEIGHT - 1; y >= 0; y--) {
      if (blockIsSolid(chunk.get(bx - chunk.originX, y, bz - chunk.originZ))) return y + 1;
    }
    return null;
  }

  /**
   * 開けた場所を探す。地表が草で、頭上と**まわり `margin` マスぶん**が空いている列。
   *
   * 地形は決定論なので、木がちょうど湧き位置に生えていると毎回そこに埋まる。
   * 真上が空いているだけでは足りない（隣に幹があると視界が塞がる）ので、
   * 周囲もまとめて見る。近い列から順に探し、最初に見つかった場所を返す。
   */
  findOpenColumn(
    x: number,
    z: number,
    radius: number,
    clearance: number,
    margin: number,
  ): { x: number; z: number; y: number } | null {
    for (let r = 0; r <= radius; r++) {
      for (let dz = -r; dz <= r; dz++) {
        for (let dx = -r; dx <= r; dx++) {
          // 外周だけ見る（内側は前の r で見終わっている）
          if (Math.max(Math.abs(dx), Math.abs(dz)) !== r) continue;

          const cx = Math.floor(x) + dx;
          const cz = Math.floor(z) + dz;
          const y = this.standingHeight(cx, cz);
          if (y === null) continue;
          if (this.getBlock(cx, y - 1, cz) !== GRASS) continue;

          if (this.isClearAround(cx, y, cz, clearance, margin)) {
            return { x: cx + 0.5, z: cz + 0.5, y };
          }
        }
      }
    }
    return null;
  }

  private isClearAround(
    cx: number,
    y: number,
    cz: number,
    clearance: number,
    margin: number,
  ): boolean {
    for (let mz = -margin; mz <= margin; mz++) {
      for (let mx = -margin; mx <= margin; mx++) {
        for (let dy = 0; dy < clearance; dy++) {
          if (this.getBlock(cx + mx, y + dy, cz + mz) !== AIR) return false;
        }
      }
    }
    return true;
  }

  /** レイキャストの対象になるメッシュ一覧。 */
  collectMeshes(target: THREE.Object3D[]): THREE.Object3D[] {
    target.length = 0;
    for (const chunk of this.chunks.values()) {
      if (chunk.opaqueMesh) target.push(chunk.opaqueMesh);
      if (chunk.transparentMesh) target.push(chunk.transparentMesh);
    }
    return target;
  }

  get chunkCount(): number {
    return this.chunks.size;
  }
}
