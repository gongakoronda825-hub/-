import * as THREE from 'three';

/** 初期版のブロック種別（仕様書 §6）。草・土・石の3種。 */
export type BlockType = 'grass' | 'dirt' | 'stone';

/** インベントリに並べる順。 */
export const BLOCK_TYPES: readonly BlockType[] = ['grass', 'dirt', 'stone'];

export const BLOCK_LABELS: Record<BlockType, string> = {
  grass: 'くさ',
  dirt: 'つち',
  stone: 'いし',
};

const TEX_SIZE = 16;

type Draw = (ctx: CanvasRenderingContext2D) => void;

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

/** ベース色にドット単位のムラを乗せた面を描く。 */
function noiseFill(
  ctx: CanvasRenderingContext2D,
  seed: number,
  base: [number, number, number],
  spread: number,
): void {
  const rand = mulberry32(seed);
  for (let y = 0; y < TEX_SIZE; y++) {
    for (let x = 0; x < TEX_SIZE; x++) {
      const d = (rand() - 0.5) * 2 * spread;
      ctx.fillStyle = `rgb(${clamp255(base[0] + d)},${clamp255(base[1] + d)},${clamp255(base[2] + d)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
}

const drawGrassTop: Draw = (ctx) => noiseFill(ctx, 11, [106, 170, 74], 22);

const drawDirt: Draw = (ctx) => noiseFill(ctx, 22, [134, 96, 67], 20);

const drawStone: Draw = (ctx) => {
  noiseFill(ctx, 44, [128, 128, 128], 18);
  // ひび割れ風の暗いドットを散らす
  const rand = mulberry32(55);
  for (let i = 0; i < 18; i++) {
    ctx.fillStyle = 'rgba(70,70,70,0.55)';
    ctx.fillRect(Math.floor(rand() * TEX_SIZE), Math.floor(rand() * TEX_SIZE), 1, 1);
  }
};

const drawGrassSide: Draw = (ctx) => {
  drawDirt(ctx);
  // 上端に草のフチを作る。境目をギザギザにするとドット絵らしく見える
  const rand = mulberry32(33);
  for (let x = 0; x < TEX_SIZE; x++) {
    const depth = 3 + Math.floor(rand() * 3);
    for (let y = 0; y < depth; y++) {
      const d = (rand() - 0.5) * 40;
      ctx.fillStyle = `rgb(${clamp255(106 + d)},${clamp255(170 + d)},${clamp255(74 + d)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
};

/**
 * 16×16 のドット絵をその場で描く。
 * 外部アセットを読まないので、ファイルを開くだけで動く / CSPにも引っかからない。
 */
function canvasOf(draw: Draw): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = TEX_SIZE;
  canvas.height = TEX_SIZE;
  draw(canvas.getContext('2d')!);
  return canvas;
}

function textureOf(draw: Draw): THREE.Texture {
  const texture = new THREE.CanvasTexture(canvasOf(draw));
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestMipmapNearestFilter;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

/**
 * BoxGeometry の material 配列の並びは [+X, -X, +Y, -Y, +Z, -Z]。
 * 草だけ上面/側面/底面を描き分ける。
 */
function buildMaterials(): Record<BlockType, THREE.Material[]> {
  const lambert = (draw: Draw) => new THREE.MeshLambertMaterial({ map: textureOf(draw) });

  const grassTop = lambert(drawGrassTop);
  const grassSide = lambert(drawGrassSide);
  const dirt = lambert(drawDirt);
  const stone = lambert(drawStone);

  return {
    grass: [grassSide, grassSide, grassTop, dirt, grassSide, grassSide],
    dirt: [dirt, dirt, dirt, dirt, dirt, dirt],
    stone: [stone, stone, stone, stone, stone, stone],
  };
}

let materials: Record<BlockType, THREE.Material[]> | null = null;

/** 種別ごとのマテリアル。全ブロックで共有する（Mesh ごとに作らない）。 */
export function materialsFor(type: BlockType): THREE.Material[] {
  materials ??= buildMaterials();
  return materials[type];
}

/** インベントリのアイコンに使う面。草は側面のほうが草と土の両方が見えて分かりやすい。 */
const ICON_DRAW: Record<BlockType, Draw> = {
  grass: drawGrassSide,
  dirt: drawDirt,
  stone: drawStone,
};

const iconCache = new Map<BlockType, string>();

/** インベントリのスロットに敷く画像（data URL）。 */
export function blockIcon(type: BlockType): string {
  let url = iconCache.get(type);
  if (!url) {
    url = canvasOf(ICON_DRAW[type]).toDataURL();
    iconCache.set(type, url);
  }
  return url;
}

/** 全ブロックで共有するジオメトリ。原点中心の 1×1×1。 */
export const BLOCK_GEOMETRY = new THREE.BoxGeometry(1, 1, 1);
