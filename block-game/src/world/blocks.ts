import * as THREE from 'three';

/**
 * ブロック種別。チャンクは Uint8Array なので、実体は数値ID。
 * 0 は空気。
 */
export const AIR = 0;
export const GRASS = 1;
export const DIRT = 2;
export const STONE = 3;
export const WOOD = 4;
export const LEAVES = 5;

export type BlockId = number;

/** インベントリに並べる、置けるブロック。 */
export const PLACEABLE: ReadonlyArray<{ id: BlockId; key: string; label: string }> = [
  { id: GRASS, key: 'grass', label: 'くさ' },
  { id: DIRT, key: 'dirt', label: 'つち' },
  { id: STONE, key: 'stone', label: 'いし' },
  { id: WOOD, key: 'wood', label: 'き' },
  { id: LEAVES, key: 'leaves', label: 'はっぱ' },
];

const KEYS: Record<BlockId, string> = {
  [AIR]: 'air',
  [GRASS]: 'grass',
  [DIRT]: 'dirt',
  [STONE]: 'stone',
  [WOOD]: 'wood',
  [LEAVES]: 'leaves',
};

export const blockKey = (id: BlockId): string => KEYS[id] ?? '?';

/** 当たり判定があるか。葉も乗れる（マイクラと同じ）。 */
export const isSolid = (id: BlockId): boolean => id !== AIR;

/**
 * 向こう側が見えないか。面カリングの判定に使う。
 *
 * 「隣が不透明でなければ面を描く」の1条件だけで、
 *   ・空気に面した面は描く
 *   ・葉に面した固体の面は描く（葉ごしに中が見えるので消してはいけない）
 *   ・葉同士の面も描く（アルファテストの穴から中が抜けて見えないように）
 * が同時に満たせる。
 */
export const isOpaque = (id: BlockId): boolean => id !== AIR && id !== LEAVES;

/** 半透明パス（アルファテスト）で描くか。 */
export const isTransparent = (id: BlockId): boolean => id === LEAVES;

// ── テクスチャアトラス ────────────────────────────────
//
// チャンクを1つの BufferGeometry にまとめる以上、マテリアルも1つに束ねる必要がある。
// 16×16 のタイルを 4×2 に並べた 64×32 のアトラスをその場で描き、UV で引く。

const TILE = 16;
const ATLAS_COLS = 4;
const ATLAS_ROWS = 2;

export const TILE_GRASS_TOP = 0;
export const TILE_GRASS_SIDE = 1;
export const TILE_DIRT = 2;
export const TILE_STONE = 3;
export const TILE_WOOD_TOP = 4;
export const TILE_WOOD_SIDE = 5;
export const TILE_LEAVES = 6;

/**
 * ブロックごとの面のタイル。並びは ChunkMesher の FACES と同じ
 * [-X, +X, -Y, +Y, -Z, +Z]。
 */
const T = TILE_GRASS_TOP;
const S = TILE_GRASS_SIDE;
const D = TILE_DIRT;
const ST = TILE_STONE;
const WT = TILE_WOOD_TOP;
const WS = TILE_WOOD_SIDE;
const L = TILE_LEAVES;

const BLOCK_TILES: Record<BlockId, readonly number[]> = {
  [AIR]: [0, 0, 0, 0, 0, 0],
  [GRASS]: [S, S, D, T, S, S],
  [DIRT]: [D, D, D, D, D, D],
  [STONE]: [ST, ST, ST, ST, ST, ST],
  [WOOD]: [WS, WS, WT, WT, WS, WS],
  [LEAVES]: [L, L, L, L, L, L],
};

export const tileOf = (id: BlockId, face: number): number => BLOCK_TILES[id][face];

/** タイル番号から UV の左下と1タイルぶんの大きさを求める。 */
export function tileUv(tile: number): { u0: number; v0: number; du: number; dv: number } {
  const col = tile % ATLAS_COLS;
  const row = Math.floor(tile / ATLAS_COLS);
  return {
    u0: col / ATLAS_COLS,
    // テクスチャの原点は左下。タイルは左上から数えているので反転する
    v0: 1 - (row + 1) / ATLAS_ROWS,
    du: 1 / ATLAS_COLS,
    dv: 1 / ATLAS_ROWS,
  };
}

/** 決定的な擬似乱数。同じ見た目を毎回再現するため Math.random は使わない。 */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const clamp255 = (v: number) => Math.max(0, Math.min(255, Math.round(v)));

type Painter = (ctx: CanvasRenderingContext2D, ox: number, oy: number) => void;

/** ベース色にドット単位のムラを乗せる。 */
function noise(
  ctx: CanvasRenderingContext2D,
  ox: number,
  oy: number,
  seed: number,
  base: [number, number, number],
  spread: number,
): void {
  const rand = mulberry32(seed);
  for (let y = 0; y < TILE; y++) {
    for (let x = 0; x < TILE; x++) {
      const d = (rand() - 0.5) * 2 * spread;
      ctx.fillStyle = `rgb(${clamp255(base[0] + d)},${clamp255(base[1] + d)},${clamp255(base[2] + d)})`;
      ctx.fillRect(ox + x, oy + y, 1, 1);
    }
  }
}

const PAINTERS: Painter[] = [];

PAINTERS[TILE_GRASS_TOP] = (ctx, ox, oy) => noise(ctx, ox, oy, 11, [106, 170, 74], 22);
PAINTERS[TILE_DIRT] = (ctx, ox, oy) => noise(ctx, ox, oy, 22, [134, 96, 67], 20);

PAINTERS[TILE_STONE] = (ctx, ox, oy) => {
  noise(ctx, ox, oy, 44, [128, 128, 128], 18);
  const rand = mulberry32(55);
  for (let i = 0; i < 18; i++) {
    ctx.fillStyle = 'rgba(70,70,70,0.55)';
    ctx.fillRect(ox + Math.floor(rand() * TILE), oy + Math.floor(rand() * TILE), 1, 1);
  }
};

PAINTERS[TILE_GRASS_SIDE] = (ctx, ox, oy) => {
  noise(ctx, ox, oy, 22, [134, 96, 67], 20);
  const rand = mulberry32(33);
  for (let x = 0; x < TILE; x++) {
    const depth = 3 + Math.floor(rand() * 3);
    for (let y = 0; y < depth; y++) {
      const d = (rand() - 0.5) * 40;
      ctx.fillStyle = `rgb(${clamp255(106 + d)},${clamp255(170 + d)},${clamp255(74 + d)})`;
      ctx.fillRect(ox + x, oy + y, 1, 1);
    }
  }
};

PAINTERS[TILE_WOOD_SIDE] = (ctx, ox, oy) => {
  noise(ctx, ox, oy, 66, [104, 78, 48], 12);
  // 縦の木目
  const rand = mulberry32(77);
  for (let x = 0; x < TILE; x++) {
    if (rand() > 0.45) continue;
    ctx.fillStyle = 'rgba(60,44,26,0.5)';
    ctx.fillRect(ox + x, oy, 1, TILE);
  }
};

PAINTERS[TILE_WOOD_TOP] = (ctx, ox, oy) => {
  noise(ctx, ox, oy, 88, [140, 108, 68], 10);
  // 年輪
  ctx.strokeStyle = 'rgba(80,58,34,0.7)';
  ctx.lineWidth = 1;
  for (const r of [2.5, 5.5]) {
    ctx.beginPath();
    ctx.arc(ox + 8, oy + 8, r, 0, Math.PI * 2);
    ctx.stroke();
  }
};

PAINTERS[TILE_LEAVES] = (ctx, ox, oy) => {
  noise(ctx, ox, oy, 99, [58, 130, 52], 26);
  // アルファテストで抜くための穴。抜きすぎると幹が透けるので控えめに。
  const rand = mulberry32(111);
  for (let y = 0; y < TILE; y++) {
    for (let x = 0; x < TILE; x++) {
      if (rand() < 0.12) ctx.clearRect(ox + x, oy + y, 1, 1);
    }
  }
};

let atlas: THREE.Texture | null = null;

/** 全チャンクで共有するアトラステクスチャ。 */
export function blockAtlas(): THREE.Texture {
  if (atlas) return atlas;

  const canvas = document.createElement('canvas');
  canvas.width = TILE * ATLAS_COLS;
  canvas.height = TILE * ATLAS_ROWS;
  const ctx = canvas.getContext('2d')!;

  for (let tile = 0; tile < PAINTERS.length; tile++) {
    const painter = PAINTERS[tile];
    if (!painter) continue;
    const col = tile % ATLAS_COLS;
    const row = Math.floor(tile / ATLAS_COLS);
    painter(ctx, col * TILE, row * TILE);
  }

  atlas = new THREE.CanvasTexture(canvas);
  atlas.magFilter = THREE.NearestFilter;
  // ミップマップを作るとタイルの端が隣とにじむ（アトラスの宿命）。
  // 距離のちらつきよりにじみのほうが目立つので、ミップマップは持たない。
  atlas.minFilter = THREE.NearestFilter;
  atlas.generateMipmaps = false;
  atlas.colorSpace = THREE.SRGBColorSpace;
  return atlas;
}

let opaqueMaterial: THREE.Material | null = null;
let transparentMaterial: THREE.Material | null = null;

export function opaqueBlockMaterial(): THREE.Material {
  opaqueMaterial ??= new THREE.MeshLambertMaterial({ map: blockAtlas() });
  return opaqueMaterial;
}

export function transparentBlockMaterial(): THREE.Material {
  // alphaTest なら透明パスの描画順を気にしなくてよい。
  // 葉は内側の面も描くので DoubleSide。
  transparentMaterial ??= new THREE.MeshLambertMaterial({
    map: blockAtlas(),
    alphaTest: 0.5,
    side: THREE.DoubleSide,
  });
  return transparentMaterial;
}

// ── インベントリ用アイコン ────────────────────────────

const ICON_TILE: Record<BlockId, number> = {
  [AIR]: 0,
  [GRASS]: TILE_GRASS_SIDE,
  [DIRT]: TILE_DIRT,
  [STONE]: TILE_STONE,
  [WOOD]: TILE_WOOD_SIDE,
  [LEAVES]: TILE_LEAVES,
};

const iconCache = new Map<BlockId, string>();

/** インベントリのスロットに敷く画像（data URL）。 */
export function blockIcon(id: BlockId): string {
  let url = iconCache.get(id);
  if (!url) {
    const canvas = document.createElement('canvas');
    canvas.width = TILE;
    canvas.height = TILE;
    const ctx = canvas.getContext('2d')!;

    // 葉は clearRect で穴を空けるので、直接描くと下地まで消える。
    // いったん別のキャンバスに描いてから、濃い緑の上に合成する。
    const layer = document.createElement('canvas');
    layer.width = TILE;
    layer.height = TILE;
    PAINTERS[ICON_TILE[id]](layer.getContext('2d')!, 0, 0);

    if (id === LEAVES) {
      ctx.fillStyle = '#2c5c28';
      ctx.fillRect(0, 0, TILE, TILE);
    }
    ctx.drawImage(layer, 0, 0);
    url = canvas.toDataURL();
    iconCache.set(id, url);
  }
  return url;
}
