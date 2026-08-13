import type * as THREE from 'three';
import { HOUSE_RESPAWN_TIME, RESIDENT_CAP } from '../core/config';
import type { ColliderSet } from '../physics/Collision';
import type { House, Town } from '../town/Town';
import { Resident } from './Resident';
import type { ResidentType } from './residentTypes';

export interface ResidentEvents {
  /** 玄関が開いて住民が出てきた瞬間。 */
  onAppear(resident: Resident): void;
  /** 追跡がはじまった瞬間。 */
  onChase(resident: Resident): void;
  /** 追跡を諦めた瞬間（＝まいた）。この後も住民は街に残る。 */
  onEscape(resident: Resident): void;
  /** 捕まった。ゲームオーバー。 */
  onCaught(resident: Resident): void;
}

/**
 * 街にいる住民の管理（追加仕様 §5〜§8）。
 *
 * 住民は「ピンポンされた家から出てくる」ものだけ。ただし**逃げ切られても
 * 家には帰らず、街を歩き回る**ので、プレイが進むほど街に溜まっていく。
 * これがゲーム後半の緊張感の正体で、上限は RESIDENT_CAP。
 *
 * 同じ家からは HOUSE_RESPAWN_TIME ごとにしか出てこない。これが無いと、
 * 1軒に貼りついて鳴らし続けたときに、その家だけで上限まで湧いてしまう。
 */
export class ResidentManager {
  private readonly residents: Resident[] = [];

  /** 家ごとの「次に住民を出せるようになるまで」の残り時間。 */
  private readonly respawn = new Map<number, number>();

  constructor(
    private readonly scene: THREE.Scene,
    private readonly colliders: ColliderSet,
    private readonly town: Town,
    private readonly events: ResidentEvents,
  ) {}

  get count(): number {
    return this.residents.length;
  }

  /** いま追跡中の住民がいるか（危険度の減衰を止める判定）。 */
  get anyChasing(): boolean {
    return this.residents.some((resident) => resident.isChasing);
  }

  /** 街を歩き回っている住民の数。UI に出して「街の危険さ」を伝える。 */
  get patrolCount(): number {
    return this.residents.filter((resident) => resident.state === 'PATROL').length;
  }

  /** いちばん進んでいる視認ゲージ。UI と、ゲームオーバー判定に使う。 */
  get maxGauge(): number {
    let max = 0;
    for (const resident of this.residents) max = Math.max(max, resident.gauge);
    return max;
  }

  /** 調整用。いま街にいる住民の状態を1行にまとめる。 */
  describeStates(): string {
    if (this.residents.length === 0) return '－';
    return this.residents.map((r) => `${r.type.name.slice(0, 2)}:${r.state}`).join(' ');
  }

  get isFull(): boolean {
    return this.residents.length >= RESIDENT_CAP;
  }

  /** その家から今すぐ住民を出せるか。 */
  canSpawnFrom(houseId: number): boolean {
    return !this.isFull && !this.respawn.has(houseId);
  }

  /**
   * 家から住民を1人出す。出せない状況なら null を返す。
   */
  spawn(house: House, type: ResidentType): Resident | null {
    if (!this.canSpawnFrom(house.id)) return null;

    const resident = new Resident(type, house.id, house.door, house.post, house.front);
    this.residents.push(resident);
    this.respawn.set(house.id, HOUSE_RESPAWN_TIME);
    this.scene.add(resident.group);
    return resident;
  }

  /**
   * 全員を1フレーム進める。捕まったら true を返す。
   * ゲームオーバーの判定そのものは呼び出し側（main）が持つ。
   */
  update(dt: number, player: THREE.Vector3): boolean {
    for (const [id, remaining] of this.respawn) {
      const next = remaining - dt;
      if (next <= 0) this.respawn.delete(id);
      else this.respawn.set(id, next);
    }

    let caught = false;

    for (let i = this.residents.length - 1; i >= 0; i--) {
      const resident = this.residents[i];
      const wasVisible = resident.group.visible;

      if (resident.update(dt, player, this.colliders, this.town)) {
        this.events.onCaught(resident);
        caught = true;
      }

      // 玄関が開いた瞬間に演出を出す
      if (!wasVisible && resident.group.visible) this.events.onAppear(resident);

      if (resident.chaseStarted) {
        resident.chaseStarted = false;
        this.events.onChase(resident);
      }

      // 追跡を諦めた瞬間にボーナス。相手は消えず、そのまま街を歩き続ける
      if (resident.gaveUp) {
        resident.gaveUp = false;
        this.events.onEscape(resident);
      }

      if (resident.finished) this.remove(i);
    }

    return caught;
  }

  private remove(index: number): void {
    const resident = this.residents[index];
    this.scene.remove(resident.group);
    resident.dispose();
    this.residents.splice(index, 1);
  }

  /** リトライ用。全員引き上げる。 */
  clear(): void {
    for (let i = this.residents.length - 1; i >= 0; i--) this.remove(i);
    this.respawn.clear();
  }
}
