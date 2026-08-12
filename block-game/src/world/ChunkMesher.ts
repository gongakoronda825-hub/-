import * as THREE from 'three';
import { CHUNK_SIZE, WORLD_HEIGHT } from '../core/config';
import type { Chunk } from './Chunk';
import { AIR, isOpaque, isTransparent, tileOf, tileUv } from './blocks';

/**
 * 立方体の6面。並びは blocks.ts の BLOCK_TILES と同じ [-X, +X, -Y, +Y, -Z, +Z]。
 * corners はブロックの原点からの相対位置と、そのタイル内での UV。
 */
const FACES = [
  {
    dir: [-1, 0, 0],
    corners: [
      { pos: [0, 1, 0], uv: [0, 1] },
      { pos: [0, 0, 0], uv: [0, 0] },
      { pos: [0, 1, 1], uv: [1, 1] },
      { pos: [0, 0, 1], uv: [1, 0] },
    ],
  },
  {
    dir: [1, 0, 0],
    corners: [
      { pos: [1, 1, 1], uv: [0, 1] },
      { pos: [1, 0, 1], uv: [0, 0] },
      { pos: [1, 1, 0], uv: [1, 1] },
      { pos: [1, 0, 0], uv: [1, 0] },
    ],
  },
  {
    dir: [0, -1, 0],
    corners: [
      { pos: [1, 0, 1], uv: [1, 0] },
      { pos: [0, 0, 1], uv: [0, 0] },
      { pos: [1, 0, 0], uv: [1, 1] },
      { pos: [0, 0, 0], uv: [0, 1] },
    ],
  },
  {
    dir: [0, 1, 0],
    corners: [
      { pos: [0, 1, 1], uv: [0, 0] },
      { pos: [1, 1, 1], uv: [1, 0] },
      { pos: [0, 1, 0], uv: [0, 1] },
      { pos: [1, 1, 0], uv: [1, 1] },
    ],
  },
  {
    dir: [0, 0, -1],
    corners: [
      { pos: [1, 0, 0], uv: [0, 0] },
      { pos: [0, 0, 0], uv: [1, 0] },
      { pos: [1, 1, 0], uv: [0, 1] },
      { pos: [0, 1, 0], uv: [1, 1] },
    ],
  },
  {
    dir: [0, 0, 1],
    corners: [
      { pos: [0, 0, 1], uv: [0, 0] },
      { pos: [1, 0, 1], uv: [1, 0] },
      { pos: [0, 1, 1], uv: [0, 1] },
      { pos: [1, 1, 1], uv: [1, 1] },
    ],
  },
] as const;

/** 面を溜めておく入れ物。不透明と半透明で1つずつ使う。 */
class Buffers {
  readonly positions: number[] = [];
  readonly normals: number[] = [];
  readonly uvs: number[] = [];
  readonly indices: number[] = [];

  get empty(): boolean {
    return this.indices.length === 0;
  }

  build(): THREE.BufferGeometry {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(this.positions, 3));
    geometry.setAttribute('normal', new THREE.Float32BufferAttribute(this.normals, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(this.uvs, 2));
    geometry.setIndex(this.indices);
    geometry.computeBoundingSphere();
    return geometry;
  }
}

/** 隣のブロックを引くための最小限のワールド。 */
export interface BlockLookup {
  getBlock(x: number, y: number, z: number): number;
}

/**
 * 面カリングでチャンクのジオメトリを組む。
 *
 * 描くのは「隣が不透明でない面」だけ。これで内部の面がすべて落ちるので、
 * 三角形の数はブロック数ではなく表面積に比例する。
 *
 * チャンクの端は隣チャンクのブロックを参照する必要があるので、
 * ChunkManager は4隣接が生成済みになるまでメッシュ化しない。
 */
export function buildChunkGeometry(
  chunk: Chunk,
  world: BlockLookup,
): { opaque: THREE.BufferGeometry | null; transparent: THREE.BufferGeometry | null } {
  const solid = new Buffers();
  const alpha = new Buffers();

  const ox = chunk.originX;
  const oz = chunk.originZ;
  // maxY より上は空なので走査しない（高さ64を毎回舐めると無駄が大きい）
  const top = Math.min(chunk.maxY, WORLD_HEIGHT - 1);

  for (let y = 0; y <= top; y++) {
    for (let lz = 0; lz < CHUNK_SIZE; lz++) {
      for (let lx = 0; lx < CHUNK_SIZE; lx++) {
        const id = chunk.get(lx, y, lz);
        if (id === AIR) continue;

        const target = isTransparent(id) ? alpha : solid;

        for (let f = 0; f < FACES.length; f++) {
          const face = FACES[f];
          const [dx, dy, dz] = face.dir;
          const neighbor = world.getBlock(ox + lx + dx, y + dy, oz + lz + dz);
          if (isOpaque(neighbor)) continue;

          addFace(target, face, lx, y, lz, tileOf(id, f));
        }
      }
    }
  }

  return {
    opaque: solid.empty ? null : solid.build(),
    transparent: alpha.empty ? null : alpha.build(),
  };
}

function addFace(
  buffers: Buffers,
  face: (typeof FACES)[number],
  lx: number,
  y: number,
  lz: number,
  tile: number,
): void {
  const base = buffers.positions.length / 3;
  const { u0, v0, du, dv } = tileUv(tile);

  for (const corner of face.corners) {
    buffers.positions.push(lx + corner.pos[0], y + corner.pos[1], lz + corner.pos[2]);
    buffers.normals.push(face.dir[0], face.dir[1], face.dir[2]);
    buffers.uvs.push(u0 + corner.uv[0] * du, v0 + corner.uv[1] * dv);
  }

  buffers.indices.push(base, base + 1, base + 2, base + 2, base + 1, base + 3);
}
