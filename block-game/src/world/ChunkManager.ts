import * as THREE from 'three';
import { CHUNK_BUDGET_MS, CHUNK_SIZE, INITIAL_RADIUS, RENDER_RADIUS } from '../core/config';
import { Chunk, toChunkCoord } from './Chunk';
import { buildChunkGeometry } from './ChunkMesher';
import type { World } from './World';
import { opaqueBlockMaterial, transparentBlockMaterial } from './blocks';

/**
 * プレイヤーの周囲のチャンクを生成し、メッシュ化し、遠いものを捨てる。
 *
 * 手順を2段に分けているのが要点：
 *   1. 半径+1 まで「データだけ」生成する（隣を一切参照しないので順不同でよい）
 *   2. 4隣接が生成済みのチャンクだけメッシュ化する
 * こうすると、チャンクの継ぎ目で面カリングの判定が狂わない。未生成の隣を
 * 空気とみなして一度描き、あとで消す…というちらつきも起きない。
 */
export class ChunkManager {
  constructor(private readonly world: World) {}

  /** 起動時に、近いところだけ先に作っておく（操作説明を読んでいる間に済ませる）。 */
  primeAround(x: number, z: number): void {
    const cx = toChunkCoord(x);
    const cz = toChunkCoord(z);

    for (let dz = -INITIAL_RADIUS - 1; dz <= INITIAL_RADIUS + 1; dz++) {
      for (let dx = -INITIAL_RADIUS - 1; dx <= INITIAL_RADIUS + 1; dx++) {
        this.world.generate(this.world.ensureChunk(cx + dx, cz + dz));
      }
    }
    for (let dz = -INITIAL_RADIUS; dz <= INITIAL_RADIUS; dz++) {
      for (let dx = -INITIAL_RADIUS; dx <= INITIAL_RADIUS; dx++) {
        const chunk = this.world.chunkAt(cx + dx, cz + dz);
        if (chunk) this.mesh(chunk);
      }
    }
  }

  /** 毎フレーム。時間予算を使い切ったらそこで止め、次のフレームに続ける。 */
  update(playerX: number, playerZ: number): void {
    const cx = toChunkCoord(playerX);
    const cz = toChunkCoord(playerZ);
    const deadline = performance.now() + CHUNK_BUDGET_MS;

    this.unloadFar(cx, cz);

    // 近い順に処理する。手前から埋まっていくほうが見た目の破綻が小さい
    for (const [dx, dz] of spiral(RENDER_RADIUS)) {
      if (performance.now() > deadline) return;

      const chunk = this.world.ensureChunk(cx + dx, cz + dz);
      if (!chunk.generated) {
        // メッシュ化に必要なので、隣も先にデータだけ作る
        this.generateWithNeighbors(chunk.cx, chunk.cz);
      }
      if (chunk.dirty && this.neighborsReady(chunk)) this.mesh(chunk);
    }
  }

  private generateWithNeighbors(cx: number, cz: number): void {
    for (let dz = -1; dz <= 1; dz++) {
      for (let dx = -1; dx <= 1; dx++) {
        this.world.generate(this.world.ensureChunk(cx + dx, cz + dz));
      }
    }
  }

  private neighborsReady(chunk: Chunk): boolean {
    for (const [dx, dz] of [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ]) {
      if (!this.world.chunkAt(chunk.cx + dx, chunk.cz + dz)?.generated) return false;
    }
    return true;
  }

  /** チャンクのジオメトリを作り直してシーンに載せる。 */
  private mesh(chunk: Chunk): void {
    if (!chunk.generated) return;

    chunk.dispose(this.world.scene);

    const { opaque, transparent } = buildChunkGeometry(chunk, this.world);
    const x = chunk.originX;
    const z = chunk.originZ;

    if (opaque) {
      chunk.opaqueMesh = new THREE.Mesh(opaque, opaqueBlockMaterial());
      chunk.opaqueMesh.position.set(x, 0, z);
      this.world.scene.add(chunk.opaqueMesh);
    }
    if (transparent) {
      chunk.transparentMesh = new THREE.Mesh(transparent, transparentBlockMaterial());
      chunk.transparentMesh.position.set(x, 0, z);
      this.world.scene.add(chunk.transparentMesh);
    }

    chunk.dirty = false;
  }

  /** 描画半径から大きく外れたチャンクを捨てる。 */
  private unloadFar(cx: number, cz: number): void {
    const limit = RENDER_RADIUS + 2;
    for (const [key, chunk] of this.world.chunks) {
      if (Math.abs(chunk.cx - cx) <= limit && Math.abs(chunk.cz - cz) <= limit) continue;
      chunk.dispose(this.world.scene);
      this.world.chunks.delete(key);
    }
  }
}

/** 中心から外へ向かう順の (dx, dz) 一覧。半径ごとにキャッシュする。 */
const spirals = new Map<number, Array<[number, number]>>();

function spiral(radius: number): Array<[number, number]> {
  let cached = spirals.get(radius);
  if (!cached) {
    cached = [];
    for (let dz = -radius; dz <= radius; dz++) {
      for (let dx = -radius; dx <= radius; dx++) cached.push([dx, dz]);
    }
    cached.sort((a, b) => a[0] * a[0] + a[1] * a[1] - (b[0] * b[0] + b[1] * b[1]));
    spirals.set(radius, cached);
  }
  return cached;
}

/** チャンク境界をまたいだかどうか（動物の湧き判定などに使う）。 */
export const sameChunk = (ax: number, az: number, bx: number, bz: number): boolean =>
  Math.floor(ax / CHUNK_SIZE) === Math.floor(bx / CHUNK_SIZE) &&
  Math.floor(az / CHUNK_SIZE) === Math.floor(bz / CHUNK_SIZE);
