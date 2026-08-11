import * as THREE from 'three';
import { BLOCK_GEOMETRY, materialsFor, type BlockType } from './blocks';

/** ブロック座標。1ブロックは [x, x+1) × [y, y+1) × [z, z+1) を占める。 */
export interface BlockPos {
  x: number;
  y: number;
  z: number;
}

const key = (x: number, y: number, z: number) => `${x},${y},${z}`;

/**
 * 固定・小規模ワールドのボクセルデータ。
 *
 * 計画書 §3.1 に従い `Map<"x,y,z", BlockType>` で持つ。隣接セルの参照が O(1) になり、
 * 当たり判定・設置位置の判定がそのまま書ける。
 *
 * 描画は計画書 §3.2 の方針どおり「1ブロック = 1 Mesh」。Raycaster がそのまま効き、
 * 破壊/設置が Mesh の出し入れだけで済む。
 */
export class World {
  /** 全ブロックの Mesh をぶら下げるグループ。レイキャストの対象でもある。 */
  readonly group = new THREE.Group();

  private readonly blocks = new Map<string, BlockType>();
  private readonly meshes = new Map<string, THREE.Mesh>();

  constructor(scene: THREE.Scene) {
    scene.add(this.group);
  }

  /** レイキャスト対象の Mesh 一覧。 */
  get meshList(): THREE.Object3D[] {
    return this.group.children;
  }

  getBlock(x: number, y: number, z: number): BlockType | undefined {
    return this.blocks.get(key(x, y, z));
  }

  isSolid(x: number, y: number, z: number): boolean {
    return this.blocks.has(key(x, y, z));
  }

  setBlock(x: number, y: number, z: number, type: BlockType): void {
    const k = key(x, y, z);
    if (this.blocks.has(k)) return;

    const mesh = new THREE.Mesh(BLOCK_GEOMETRY, materialsFor(type));
    // Mesh は原点中心なので、セルの中心に置く。
    mesh.position.set(x + 0.5, y + 0.5, z + 0.5);
    mesh.userData.block = { x, y, z } satisfies BlockPos;

    this.blocks.set(k, type);
    this.meshes.set(k, mesh);
    this.group.add(mesh);
  }

  removeBlock(x: number, y: number, z: number): boolean {
    const k = key(x, y, z);
    if (!this.blocks.has(k)) return false;

    const mesh = this.meshes.get(k);
    if (mesh) this.group.remove(mesh);

    this.blocks.delete(k);
    this.meshes.delete(k);
    return true;
  }

  /** Mesh からブロック座標を取り出す。 */
  static blockOf(object: THREE.Object3D): BlockPos | undefined {
    return object.userData.block as BlockPos | undefined;
  }

  get blockCount(): number {
    return this.blocks.size;
  }
}

const GROUND_RADIUS = 12;

/**
 * 初期ワールドを組み立てる。
 *
 * 自動地形生成は仕様書 §12 で禁止されているので、地面を敷いて数個積むだけの
 * ハードコードにしてある。
 */
export function buildInitialWorld(world: World): void {
  // 地面: y=0 が草、y=-1 と y=-2 が土/石。落ちても抜けないよう3層ぶん敷く。
  for (let x = -GROUND_RADIUS; x < GROUND_RADIUS; x++) {
    for (let z = -GROUND_RADIUS; z < GROUND_RADIUS; z++) {
      world.setBlock(x, 0, z, 'grass');
      world.setBlock(x, -1, z, 'dirt');
      world.setBlock(x, -2, z, 'stone');
    }
  }

  // 目印になる小さな塔（登り降りと設置の練習台）
  const tower: Array<[number, number, number]> = [
    [-3, 1, -3], [-3, 2, -3], [-3, 3, -3],
    [-2, 1, -3], [-2, 2, -3],
    [-3, 1, -2], [-3, 2, -2],
    [-2, 1, -2],
  ];
  for (const [x, y, z] of tower) world.setBlock(x, y, z, 'stone');

  // 階段状の土の段差
  for (let i = 0; i < 4; i++) {
    for (let y = 1; y <= i + 1; y++) {
      world.setBlock(3 + i, y, 2, 'dirt');
    }
  }

  // 正面の壁。破壊の的にちょうどよい
  for (let x = -1; x <= 1; x++) {
    for (let y = 1; y <= 3; y++) {
      world.setBlock(x, y, -5, x === 0 && y === 2 ? 'grass' : 'stone');
    }
  }

  // 浮いたブロック（重力が効かないことの確認と、下面への設置テスト用）
  world.setBlock(2, 4, -2, 'grass');
}
