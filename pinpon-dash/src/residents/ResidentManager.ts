import type * as THREE from 'three';
import { RESIDENT_CAP } from '../core/config';
import type { ColliderSet } from '../physics/Collision';
import type { House } from '../town/Town';
import { Resident } from './Resident';
import type { ResidentType } from './residentTypes';

export interface ResidentEvents {
  /** 玄関が開いて住民が出てきた瞬間。 */
  onAppear(resident: Resident): void;
  /** 追跡がはじまった瞬間。 */
  onChase(resident: Resident): void;
  /** 追跡してきた住民をまいた（家に帰った）。 */
  onEscape(resident: Resident): void;
  /** 捕まった。ゲームオーバー。 */
  onCaught(resident: Resident): void;
}

/**
 * 外に出ている住民の管理。
 *
 * 住民は「ピンポンされた家から出てくる」ものだけで、街をうろついている
 * 住民は最初からいない。危険度が上がるほど出現しやすくなるので、
 * プレイヤーの行動と街の騒がしさが直結する（指示書 §3）。
 */
export class ResidentManager {
  private readonly residents: Resident[] = [];

  /** すでに住民が外に出ている家の id。同じ家から二重に出てこないようにする。 */
  private readonly occupied = new Set<number>();

  constructor(
    private readonly scene: THREE.Scene,
    private readonly colliders: ColliderSet,
    private readonly events: ResidentEvents,
  ) {}

  get count(): number {
    return this.residents.length;
  }

  /** いま追跡中の住民がいるか（危険度の減衰を止める判定）。 */
  get anyChasing(): boolean {
    return this.residents.some((resident) => resident.isChasing);
  }

  /** いちばん進んでいる視認ゲージ。UI と、ゲームオーバー判定に使う。 */
  get maxGauge(): number {
    let max = 0;
    for (const resident of this.residents) max = Math.max(max, resident.gauge);
    return max;
  }

  /** 調整用。いま外にいる住民の状態を1行にまとめる。 */
  describeStates(): string {
    if (this.residents.length === 0) return '－';
    return this.residents.map((r) => `${r.type.name.slice(0, 2)}:${r.state}`).join(' ');
  }

  isOccupied(houseId: number): boolean {
    return this.occupied.has(houseId);
  }

  get isFull(): boolean {
    return this.residents.length >= RESIDENT_CAP;
  }

  /**
   * 家から住民を1人出す。すでにその家から出ているか、上限に達していれば何もしない。
   * 戻り値は実際に出てきたかどうか。
   */
  spawn(house: House, type: ResidentType): Resident | null {
    if (this.isFull || this.occupied.has(house.id)) return null;

    const resident = new Resident(type, house.id, house.door, house.post, house.front);
    this.residents.push(resident);
    this.occupied.add(house.id);
    this.scene.add(resident.group);
    return resident;
  }

  /**
   * 全員を1フレーム進める。捕まったら true を返す。
   * ゲームオーバーの判定そのものは呼び出し側（Game）が持つ。
   */
  update(dt: number, player: THREE.Vector3): boolean {
    let caught = false;

    for (let i = this.residents.length - 1; i >= 0; i--) {
      const resident = this.residents[i];
      const wasVisible = resident.group.visible;

      if (resident.update(dt, player, this.colliders)) {
        this.events.onCaught(resident);
        caught = true;
      }

      // 玄関が開いた瞬間に演出を出す
      if (!wasVisible && resident.group.visible) this.events.onAppear(resident);

      if (resident.chaseStarted) {
        resident.chaseStarted = false;
        this.events.onChase(resident);
      }

      if (resident.finished) {
        // 追いかけてきた相手をまいた場合だけボーナス
        if (resident.everChased) this.events.onEscape(resident);
        this.remove(i);
      }
    }

    return caught;
  }

  private remove(index: number): void {
    const resident = this.residents[index];
    this.scene.remove(resident.group);
    resident.dispose();
    this.occupied.delete(resident.houseId);
    this.residents.splice(index, 1);
  }

  /** リトライ用。全員引き上げる。 */
  clear(): void {
    for (let i = this.residents.length - 1; i >= 0; i--) this.remove(i);
    this.occupied.clear();
  }
}
