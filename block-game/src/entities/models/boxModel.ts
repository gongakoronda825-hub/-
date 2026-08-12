import * as THREE from 'three';

/**
 * 箱モデルの共通部品。
 *
 * 個体ごとに Mesh は作るが、**ジオメトリとマテリアルは種ごとに1つを共有**する。
 * 1×1×1 のジオメトリを1つ持ち、Mesh 側の scale で各パーツの大きさを出す。
 */
export const UNIT_BOX = new THREE.BoxGeometry(1, 1, 1);

/** 出来上がったモデル。脚は歩行アニメのために参照を持っておく。 */
export interface AnimalModel {
  group: THREE.Group;
  legs: THREE.Object3D[];
  head: THREE.Object3D;
}

/**
 * パーツを1つ足す。位置は「足元中心」を原点としたモデル座標。
 *
 * 返すのは**スケールのかかっていない** Object3D のピボット。Mesh を直接返すと、
 * そこに子パーツ（鼻や角）を足したときに親のスケールで歪んでしまう。
 * 脚は付け根で振りたいので、ピボットをパーツの上端に置ける。
 */
export function addPart(
  parent: THREE.Object3D,
  material: THREE.Material,
  size: [number, number, number],
  center: [number, number, number],
  pivotTop = false,
): THREE.Object3D {
  const mesh = new THREE.Mesh(UNIT_BOX, material);
  mesh.scale.set(size[0], size[1], size[2]);

  const pivot = new THREE.Object3D();
  if (pivotTop) {
    pivot.position.set(center[0], center[1] + size[1] / 2, center[2]);
    mesh.position.set(0, -size[1] / 2, 0);
  } else {
    pivot.position.set(center[0], center[1], center[2]);
  }

  pivot.add(mesh);
  parent.add(pivot);
  return pivot;
}

/** 決定的な擬似乱数。テクスチャを毎回同じ見た目にする。 */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * まだら模様のテクスチャを作る。ブロックと同じドット絵の質感に寄せる。
 */
export function patchTexture(
  seed: number,
  base: string,
  patch: string,
  patches: number,
): THREE.Texture {
  const size = 16;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);

  const rand = mulberry32(seed);
  ctx.fillStyle = patch;
  for (let i = 0; i < patches; i++) {
    const w = 3 + Math.floor(rand() * 4);
    const h = 3 + Math.floor(rand() * 4);
    ctx.fillRect(Math.floor(rand() * size), Math.floor(rand() * size), w, h);
  }

  // ドット単位の陰影を軽く乗せる
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      if (rand() > 0.25) continue;
      ctx.fillStyle = `rgba(0,0,0,${0.05 + rand() * 0.08})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
