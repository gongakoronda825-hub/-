import * as THREE from 'three';
import type { ResidentType } from '../residentTypes';

/**
 * デフォルメした住民の3Dモデル（指示書 §14）。
 *
 * 箱だけで組む。頭は大きめ、手足は短め。等身を崩しておくと、
 * ただの住宅街で起きている騒ぎのバカバカしさが出る。
 *
 * 腕と脚は Group を親にして、肩・股の位置を回転の中心にしている。
 * ジオメトリを下へずらしておかないと、真ん中で折れたように振れてしまう。
 */
export interface ResidentModel {
  readonly group: THREE.Group;
  readonly legs: THREE.Group[];
  readonly arms: THREE.Group[];
  readonly head: THREE.Group;
  /** 使い終わったら呼ぶ。ジオメトリとマテリアルを解放する。 */
  dispose(): void;
}

export function buildResident(type: ResidentType): ResidentModel {
  const { colors, look } = type;
  const group = new THREE.Group();

  const created: (THREE.BufferGeometry | THREE.Material)[] = [];

  const material = (color: number): THREE.MeshLambertMaterial => {
    const m = new THREE.MeshLambertMaterial({ color });
    created.push(m);
    return m;
  };

  const box = (
    w: number,
    h: number,
    d: number,
    color: number,
  ): THREE.Mesh => {
    const geometry = new THREE.BoxGeometry(w, h, d);
    created.push(geometry);
    return new THREE.Mesh(geometry, material(color));
  };

  const scale = look.heightScale;
  const hipY = 0.72 * scale;
  const shoulderY = 1.32 * scale;

  // 胴
  const torso = box(0.62, 0.66 * scale, 0.36, colors.shirt);
  torso.position.y = hipY + (0.66 * scale) / 2;
  group.add(torso);

  // 頭（+Z が正面）
  const head = new THREE.Group();
  head.position.y = shoulderY + 0.1 * scale;
  group.add(head);

  const headSize = 0.52 * look.headScale;
  const skull = box(headSize, headSize, headSize, colors.skin);
  skull.position.y = headSize / 2;
  head.add(skull);

  const hair = box(headSize * 1.04, headSize * 0.34, headSize * 1.04, colors.hair);
  hair.position.y = headSize * 0.92;
  head.add(hair);

  // 目。白目は作らず、黒い点だけ。遠くからでも表情が読める。
  for (const side of [-1, 1]) {
    const eye = box(0.075, 0.11, 0.04, 0x241d1a);
    eye.position.set(side * headSize * 0.22, headSize * 0.56, headSize / 2 + 0.02);
    head.add(eye);

    // 眉。吊り上げるほど怒って見える。ふつうの住民は水平。
    const brow = box(0.16, 0.05, 0.04, colors.hair);
    brow.position.set(side * headSize * 0.22, headSize * 0.76, headSize / 2 + 0.02);
    brow.rotation.z = (side * -look.browAngle * Math.PI) / 180;
    head.add(brow);
  }

  // 口。大きく開けっぱなしにしておくと、叫んでいるように見える。
  const mouth = box(0.18, 0.1, 0.04, 0x6b2b2b);
  mouth.position.set(0, headSize * 0.24, headSize / 2 + 0.02);
  head.add(mouth);

  const legs: THREE.Group[] = [];
  const arms: THREE.Group[] = [];

  // 脚。股（hipY）を軸に振る。
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(side * 0.16, hipY, 0);
    const leg = box(0.2, hipY, 0.2, colors.pants);
    leg.position.y = -hipY / 2;
    pivot.add(leg);
    group.add(pivot);
    legs.push(pivot);
  }

  // 腕。肩を軸に振る。
  const armLength = 0.58 * scale;
  for (const side of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(side * 0.38, shoulderY, 0);
    const arm = box(0.16, armLength, 0.16, colors.shirt);
    arm.position.y = -armLength / 2;
    pivot.add(arm);
    const hand = box(0.17, 0.15, 0.17, colors.skin);
    hand.position.y = -armLength;
    pivot.add(hand);
    group.add(pivot);
    arms.push(pivot);
  }

  return {
    group,
    legs,
    arms,
    head,
    dispose(): void {
      for (const item of created) item.dispose();
    },
  };
}
