import * as THREE from 'three';
import { addPart, patchTexture, type AnimalModel } from './boxModel';

let materials: { wool: THREE.Material; skin: THREE.Material } | null = null;

function sheepMaterials() {
  materials ??= {
    // ほとんど白。ムラだけ入れてモコモコに見せる
    wool: new THREE.MeshLambertMaterial({ map: patchTexture(9317, '#f4f2ec', '#e2ded2', 10) }),
    skin: new THREE.MeshLambertMaterial({ color: 0xd8c6b4 }),
  };
  return materials;
}

/**
 * 羊。胴を一回り大きく（モコモコ）、牛より短い。
 * モデルは +Z を正面として組む。
 */
export function buildSheepModel(): AnimalModel {
  const { wool, skin } = sheepMaterials();
  const group = new THREE.Group();

  // 胴。牛より太くて短い
  addPart(group, wool, [1.0, 0.85, 1.05], [0, 0.9, 0]);

  // 頭は羊毛から出ているので肌色
  const head = addPart(group, skin, [0.42, 0.45, 0.45], [0, 0.95, 0.7]);
  // 耳
  addPart(head, skin, [0.12, 0.08, 0.2], [-0.28, 0.12, -0.05]);
  addPart(head, skin, [0.12, 0.08, 0.2], [0.28, 0.12, -0.05]);
  // 額の羊毛
  addPart(head, wool, [0.44, 0.16, 0.2], [0, 0.24, -0.06]);

  const legs: THREE.Object3D[] = [];
  for (const [x, z] of [
    [-0.3, 0.32],
    [0.3, 0.32],
    [-0.3, -0.32],
    [0.3, -0.32],
  ]) {
    legs.push(addPart(group, skin, [0.2, 0.5, 0.2], [x, 0, z], true));
  }

  return { group, legs, head };
}
