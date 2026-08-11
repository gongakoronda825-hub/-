import * as THREE from 'three';

/** 初期版のブロック種別（仕様書 §6）。草・土・石の3種のみ。 */
export type BlockType = 'grass' | 'dirt' | 'stone';

/** 「置く」で生成されるブロック。インベントリは作らないので固定。 */
export const PLACEABLE_BLOCK: BlockType = 'stone';

const TEX_SIZE = 16;

/**
 * 16×16 のドットテクスチャをその場で生成する。
 * 外部アセットを読まないので、ファイルを開くだけで動く / CSPにも引っかからない。
 */
function makeTexture(draw: (ctx: CanvasRenderingContext2D) => void): THREE.Texture {
  const canvas = document.createElement('canvas');
  canvas.width = TEX_SIZE;
  canvas.height = TEX_SIZE;
  const ctx = canvas.getContext('2d')!;
  draw(ctx);

  const texture = new THREE.CanvasTexture(canvas);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestMipmapNearestFilter;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
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

/** ベース色にドット単位のムラを乗せた面を描く。 */
function noiseFill(
  ctx: CanvasRenderingContext2D,
  seed: number,
  base: [number, number, number],
  spread: number,
  y0 = 0,
  y1 = TEX_SIZE,
): void {
  const rand = mulberry32(seed);
  for (let y = y0; y < y1; y++) {
    for (let x = 0; x < TEX_SIZE; x++) {
      const d = (rand() - 0.5) * 2 * spread;
      const r = Math.max(0, Math.min(255, Math.round(base[0] + d)));
      const g = Math.max(0, Math.min(255, Math.round(base[1] + d)));
      const b = Math.max(0, Math.min(255, Math.round(base[2] + d)));
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
}

const grassTop = () => makeTexture((ctx) => noiseFill(ctx, 11, [106, 170, 74], 22));
const dirt = () => makeTexture((ctx) => noiseFill(ctx, 22, [134, 96, 67], 20));
const stone = () => makeTexture((ctx) => makeStone(ctx));
const grassSide = () =>
  makeTexture((ctx) => {
    noiseFill(ctx, 22, [134, 96, 67], 20);
    // 上端に草のフチを作る。境目をギザギザにするとドット絵らしく見える。
    const rand = mulberry32(33);
    for (let x = 0; x < TEX_SIZE; x++) {
      const depth = 3 + Math.floor(rand() * 3);
      for (let y = 0; y < depth; y++) {
        const d = (rand() - 0.5) * 40;
        ctx.fillStyle = `rgb(${106 + d | 0},${170 + d | 0},${74 + d | 0})`;
        ctx.fillRect(x, y, 1, 1);
      }
    }
  });

function makeStone(ctx: CanvasRenderingContext2D): void {
  noiseFill(ctx, 44, [128, 128, 128], 18);
  // ひび割れ風の暗いドットを散らす
  const rand = mulberry32(55);
  for (let i = 0; i < 18; i++) {
    ctx.fillStyle = 'rgba(70,70,70,0.55)';
    ctx.fillRect(Math.floor(rand() * TEX_SIZE), Math.floor(rand() * TEX_SIZE), 1, 1);
  }
}

/**
 * BoxGeometry の material 配列の並びは [+X, -X, +Y, -Y, +Z, -Z]。
 * 草だけ上面/側面/底面を描き分ける。
 */
function buildMaterials(): Record<BlockType, THREE.Material[]> {
  const lambert = (map: THREE.Texture) => new THREE.MeshLambertMaterial({ map });

  const grassTopMat = lambert(grassTop());
  const grassSideMat = lambert(grassSide());
  const dirtMat = lambert(dirt());
  const stoneMat = lambert(stone());

  return {
    grass: [grassSideMat, grassSideMat, grassTopMat, dirtMat, grassSideMat, grassSideMat],
    dirt: [dirtMat, dirtMat, dirtMat, dirtMat, dirtMat, dirtMat],
    stone: [stoneMat, stoneMat, stoneMat, stoneMat, stoneMat, stoneMat],
  };
}

let materials: Record<BlockType, THREE.Material[]> | null = null;

/** 種別ごとのマテリアル。全ブロックで共有する（Mesh ごとに作らない）。 */
export function materialsFor(type: BlockType): THREE.Material[] {
  materials ??= buildMaterials();
  return materials[type];
}

/** 全ブロックで共有するジオメトリ。原点中心の 1×1×1。 */
export const BLOCK_GEOMETRY = new THREE.BoxGeometry(1, 1, 1);
