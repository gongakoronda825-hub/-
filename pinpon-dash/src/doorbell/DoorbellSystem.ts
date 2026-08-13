import * as THREE from 'three';
import {
  DOORBELL_COOLDOWN,
  DOORBELL_FACING,
  DOORBELL_RANGE,
} from '../core/config';
import type { GameState } from '../core/GameState';
import type { House, Town } from '../town/Town';
import type { ResidentManager } from '../residents/ResidentManager';
import { pickResidentType } from '../residents/residentTypes';

/** インターホンが光る色。近づいたときだけ明るくする。 */
const IDLE_COLOR = 0xff7a6a;
const ACTIVE_COLOR = 0xfff36a;

export interface PingResult {
  readonly points: number;
  /** 何連続目か。 */
  readonly combo: number;
  /** その家から住民が出てきたか。 */
  readonly spawned: boolean;
  /** つられて別の家からも出てきたか。 */
  readonly extra: boolean;
}

/**
 * ピンポンの中核（指示書 §5 / 追加仕様 §1〜§4）。
 *
 * 「近づく → ボタンが出る → 押した瞬間に鳴る」だけ。確認画面も長押しも無い。
 * ここに一拍でも入れると、このゲームでいちばん大事な
 *「もう一回押したい」という手癖が育たなくなる。
 *
 * ポイントとコンボの計算は GameState、誰が出てくるかはここが決める。
 */
export class DoorbellSystem {
  /** いま押せるインターホン。無ければ null。 */
  private target: House | null = null;

  /** 家ごとの連打防止タイマー。 */
  private readonly cooldowns = new Map<number, number>();

  private readonly toDoorbell = new THREE.Vector3();

  constructor(
    private readonly town: Town,
    private readonly state: GameState,
    private readonly residents: ResidentManager,
  ) {}

  /** ボタンを出すかどうか。UI はこれを見るだけでよい。 */
  get available(): House | null {
    return this.target;
  }

  /** コンボが乗っている家までの距離。乗っていなければ null（コンボ保持の判定用）。 */
  distanceToCombo(position: THREE.Vector3): number | null {
    const id = this.state.comboHouseId;
    if (id === null) return null;
    const house = this.town.houses[id];
    if (!house) return null;
    return Math.hypot(house.doorbell.x - position.x, house.doorbell.z - position.z);
  }

  /**
   * 毎フレーム、いちばん近くて正面にあるインターホンを1つ選ぶ。
   *
   * @param position プレイヤーの足元
   * @param forward  プレイヤーの視線（水平）
   */
  update(dt: number, position: THREE.Vector3, forward: THREE.Vector3): void {
    for (const [id, remaining] of this.cooldowns) {
      const next = remaining - dt;
      if (next <= 0) this.cooldowns.delete(id);
      else this.cooldowns.set(id, next);
    }

    const previous = this.target;
    this.target = this.findNearest(position, forward);

    if (previous !== this.target) {
      if (previous) this.setGlow(previous, false);
      if (this.target) this.setGlow(this.target, true);
    }
  }

  private findNearest(position: THREE.Vector3, forward: THREE.Vector3): House | null {
    let best: House | null = null;
    let bestDistance = DOORBELL_RANGE;
    const limit = Math.cos((DOORBELL_FACING * Math.PI) / 360);

    for (const house of this.town.houses) {
      this.toDoorbell.set(house.doorbell.x - position.x, 0, house.doorbell.z - position.z);
      const distance = this.toDoorbell.length();
      if (distance > bestDistance) continue;

      // 真横や背中側のインターホンを拾わないように、向きも見る
      if (distance > 0.4) {
        this.toDoorbell.divideScalar(distance);
        if (this.toDoorbell.dot(forward) < limit) continue;
      }

      best = house;
      bestDistance = distance;
    }
    return best;
  }

  private setGlow(house: House, on: boolean): void {
    const material = house.button.material as THREE.MeshLambertMaterial;
    material.color.setHex(on ? ACTIVE_COLOR : IDLE_COLOR);
    material.emissive.setHex(on ? 0x552200 : 0x000000);
  }

  /**
   * ピンポンする。押せる状態でなければ null を返す。
   *
   * 同じ家を続けて鳴らすほどポイントが跳ね上がる（GameState 側）。
   * その代わり、住民の出てくる確率もコンボの分だけ上がる。
   */
  ping(): PingResult | null {
    const house = this.target;
    if (!house || this.cooldowns.has(house.id)) return null;

    this.cooldowns.set(house.id, DOORBELL_COOLDOWN);

    const tier = this.state.tier;
    const chance = this.state.spawnChance();
    const { points, combo } = this.state.ping(house.id);

    let spawned = false;
    if (Math.random() < chance) {
      spawned = this.residents.spawn(house, pickResidentType(tier.weights)) !== null;
      if (spawned) this.state.onResidentAppeared(house.id);
    }

    // 危険度が高いと近所も騒ぎ出す。逃げ道を塞がれるのがここから始まる
    let extra = false;
    if (tier.extra > 0 && Math.random() < tier.extra) {
      const neighbor = this.pickNeighborHouse(house);
      if (neighbor) {
        extra = this.residents.spawn(neighbor, pickResidentType(tier.weights)) !== null;
      }
    }

    return { points, combo, spawned, extra };
  }

  /** 鳴らした家の近所で、いま住民を出せる家を1軒選ぶ。 */
  private pickNeighborHouse(house: House): House | null {
    const candidates = this.town.houses.filter((other) => {
      if (other.id === house.id || !this.residents.canSpawnFrom(other.id)) return false;
      const distance = Math.hypot(
        other.center.x - house.center.x,
        other.center.z - house.center.z,
      );
      return distance < 26;
    });

    if (candidates.length === 0) return null;
    return candidates[Math.floor(Math.random() * candidates.length)];
  }

  /** リトライ用。 */
  reset(): void {
    if (this.target) this.setGlow(this.target, false);
    this.target = null;
    this.cooldowns.clear();
  }
}
