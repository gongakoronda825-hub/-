import * as THREE from 'three';
import { CHUNK_SIZE, WORLD_HEIGHT } from '../core/config';
import { AIR, type BlockId } from './blocks';

export const chunkKey = (cx: number, cz: number): string => `${cx},${cz}`;

/** ワールド座標 → チャンク座標。負の側でも正しく切り下げる。 */
export const toChunkCoord = (v: number): number => Math.floor(v / CHUNK_SIZE);

/**
 * 16×16 列 × 高さ64 のボクセル。
 *
 * 1ブロック1 Mesh では広いワールドが持たないので、データは型付き配列、
 * 描画はチャンク単位の結合ジオメトリにする。
 */
export class Chunk {
  readonly voxels = new Uint8Array(CHUNK_SIZE * CHUNK_SIZE * WORLD_HEIGHT);

  /** 地形と木を書き込み終わったか。メッシュ化は隣が揃うまで待つ。 */
  generated = false;

  /** メッシュを作り直す必要があるか。 */
  dirty = true;

  /** このチャンクの最も高いブロックの y。メッシュ化の走査範囲を切るのに使う。 */
  maxY = 0;

  opaqueMesh: THREE.Mesh | null = null;
  transparentMesh: THREE.Mesh | null = null;

  constructor(
    readonly cx: number,
    readonly cz: number,
  ) {}

  /** チャンク内のローカル座標 → 配列インデックス。 */
  private static index(lx: number, y: number, lz: number): number {
    return (y * CHUNK_SIZE + lz) * CHUNK_SIZE + lx;
  }

  /** ローカル座標で読む。範囲外は空気。 */
  get(lx: number, y: number, lz: number): BlockId {
    if (lx < 0 || lx >= CHUNK_SIZE || lz < 0 || lz >= CHUNK_SIZE) return AIR;
    if (y < 0 || y >= WORLD_HEIGHT) return AIR;
    return this.voxels[Chunk.index(lx, y, lz)];
  }

  /** ローカル座標で書く。 */
  set(lx: number, y: number, lz: number, id: BlockId): void {
    if (lx < 0 || lx >= CHUNK_SIZE || lz < 0 || lz >= CHUNK_SIZE) return;
    if (y < 0 || y >= WORLD_HEIGHT) return;
    this.voxels[Chunk.index(lx, y, lz)] = id;
    if (id !== AIR && y > this.maxY) this.maxY = y;
  }

  /** ワールド座標での原点（このチャンクの最小角）。 */
  get originX(): number {
    return this.cx * CHUNK_SIZE;
  }

  get originZ(): number {
    return this.cz * CHUNK_SIZE;
  }

  /** シーンから外して GPU リソースを解放する。 */
  dispose(scene: THREE.Scene): void {
    for (const mesh of [this.opaqueMesh, this.transparentMesh]) {
      if (!mesh) continue;
      scene.remove(mesh);
      mesh.geometry.dispose();
    }
    this.opaqueMesh = null;
    this.transparentMesh = null;
  }
}
