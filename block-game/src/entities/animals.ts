import { ANIMAL_SPEED } from '../core/config';
import type { AnimalModel } from './models/boxModel';
import { buildCowModel } from './models/buildCowModel';
import { buildSheepModel } from './models/buildSheepModel';

export type AnimalKind = 'cow' | 'sheep';

export interface AnimalSpecies {
  kind: AnimalKind;
  label: string;
  /** AABB。当たり判定はこの大きさで、見た目のモデルとは別。 */
  width: number;
  height: number;
  depth: number;
  speed: number;
  /** 湧きの重み。大きいほどよく湧く。 */
  spawnWeight: number;
  build: () => AnimalModel;
}

/**
 * 種別の定義。行動は共通で、**違いは見た目と湧きのパラメータだけ**。
 * 種を増やすときはここに1つ足せばよく、クラスは増やさない。
 */
export const SPECIES: Record<AnimalKind, AnimalSpecies> = {
  cow: {
    kind: 'cow',
    label: 'うし',
    width: 0.9,
    height: 1.3,
    depth: 1.4,
    speed: ANIMAL_SPEED,
    spawnWeight: 1,
    build: buildCowModel,
  },
  sheep: {
    kind: 'sheep',
    label: 'ひつじ',
    width: 0.9,
    height: 1.3,
    depth: 1.0,
    speed: ANIMAL_SPEED,
    spawnWeight: 1,
    build: buildSheepModel,
  },
};

const ALL = Object.values(SPECIES);
const TOTAL_WEIGHT = ALL.reduce((sum, s) => sum + s.spawnWeight, 0);

/** 重み付きでランダムに1種選ぶ。 */
export function randomSpecies(): AnimalSpecies {
  let roll = Math.random() * TOTAL_WEIGHT;
  for (const species of ALL) {
    roll -= species.spawnWeight;
    if (roll <= 0) return species;
  }
  return ALL[ALL.length - 1];
}
