import * as THREE from 'three';
import { addPart, patchTexture, type AnimalModel } from './boxModel';

let materials: { hide: THREE.Material; dark: THREE.Material; horn: THREE.Material } | null = null;

/** 種ごとに1組だけ作って全個体で使い回す。 */
function cowMaterials() {
  materials ??= {
    hide: new THREE.MeshLambertMaterial({ map: patchTexture(4211, '#f2f0ea', '#2f2b28', 7) }),
    dark: new THREE.MeshLambertMaterial({ color: 0x3a3330 }),
    horn: new THREE.MeshLambertMaterial({ color: 0xd8cfae }),
  };
  return materials;
}

/**
 * 牛。白×黒のまだら、胴が長め。
 * モデルは +Z を正面として組む（Animal が速度ベクトルの向きへ回す）。
 */
export function buildCowModel(): AnimalModel {
  const { hide, dark, horn } = cowMaterials();
  const group = new THREE.Group();

  // 胴（幅0.9 × 高さ0.7 × 奥行1.4、脚の上）
  addPart(group, hide, [0.9, 0.7, 1.4], [0, 0.9, 0]);

  // 頭。胴の前側に少し突き出す
  const head = addPart(group, hide, [0.55, 0.5, 0.5], [0, 1.0, 0.85]);
  // 鼻づら
  addPart(head, dark, [0.35, 0.25, 0.12], [0, -0.24, 0.53]);
  // 角
  addPart(head, horn, [0.1, 0.12, 0.1], [-0.3, 0.45, 0]);
  addPart(head, horn, [0.1, 0.12, 0.1], [0.3, 0.45, 0]);

  // 脚4本。付け根を軸に振れるようにする
  const legs: THREE.Object3D[] = [];
  for (const [x, z] of [
    [-0.28, 0.45],
    [0.28, 0.45],
    [-0.28, -0.45],
    [0.28, -0.45],
  ]) {
    legs.push(addPart(group, dark, [0.24, 0.55, 0.24], [x, 0, z], true));
  }

  return { group, legs, head };
}
