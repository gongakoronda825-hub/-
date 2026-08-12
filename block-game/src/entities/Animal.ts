import {
  AI_TICK,
  IDLE_MAX,
  IDLE_MIN,
  WANDER_MAX,
  WANDER_MIN,
} from '../core/config';
import type { World } from '../world/World';
import { Entity } from './Entity';
import type { AnimalSpecies } from './animals';
import type { AnimalModel } from './models/boxModel';

const between = (min: number, max: number): number => min + Math.random() * (max - min);

/**
 * パッシブな動物。うろつき ↔ 立ち止まり だけの単純なステートマシン。
 *
 * 逃げも寄りもせず、繁殖もドロップもしない。歩き回るだけの装飾。
 *
 * 判断（向きを変える・状態を切り替える）は AI_TICK ごと。
 * 物理（重力・衝突）は毎フレーム。頭数が増えても効くのは物理だけになる。
 */
export class Animal extends Entity {
  private readonly model: AnimalModel;

  private state: 'wander' | 'idle' = 'idle';
  private stateTimer = 0;
  private aiTimer = 0;

  /** 進行方向（水平の単位ベクトル）。 */
  private dirX = 0;
  private dirZ = 1;

  /** 脚を振るための位相。 */
  private walkPhase = 0;

  constructor(
    world: World,
    readonly species: AnimalSpecies,
    x: number,
    y: number,
    z: number,
  ) {
    super(world, species.width, species.height, species.depth);
    this.position.set(x, y, z);

    this.model = species.build();
    this.group.add(this.model.group);
    this.group.position.copy(this.position);

    // 個体ごとにばらけさせる。全部が同時に歩き出すと不自然
    this.stateTimer = between(0, IDLE_MAX);
    this.pickDirection();
  }

  protected think(dt: number): void {
    this.aiTimer += dt;
    if (this.aiTimer >= AI_TICK) {
      this.decide(this.aiTimer);
      this.aiTimer = 0;
    }

    const speed = this.state === 'wander' ? this.species.speed : 0;
    this.velocity.x = this.dirX * speed;
    this.velocity.z = this.dirZ * speed;

    this.animate(dt, speed);
  }

  /** AI_TICK ごとの判断。 */
  private decide(elapsed: number): void {
    this.stateTimer -= elapsed;

    if (this.stateTimer <= 0) {
      if (this.state === 'wander') {
        this.state = 'idle';
        this.stateTimer = between(IDLE_MIN, IDLE_MAX);
      } else {
        this.state = 'wander';
        this.stateTimer = between(WANDER_MIN, WANDER_MAX);
        this.pickDirection();
      }
      return;
    }

    // 歩いている途中で前が塞がれたら向きを選び直す。
    // 1段の段差は登れるので「塞がれ」には数えない。
    if (this.state === 'wander' && this.isBlockedAhead(this.dirX, this.dirZ, this.depth / 2 + 0.4)) {
      this.pickDirection();
    }
  }

  private pickDirection(): void {
    const angle = Math.random() * Math.PI * 2;
    this.dirX = Math.sin(angle);
    this.dirZ = Math.cos(angle);
    // モデルは +Z が正面なので、その向きへ回す
    this.group.rotation.y = Math.atan2(this.dirX, this.dirZ);
  }

  /** 歩いているときだけ脚を振る。前後で位相を反転させて交互に見せる。 */
  private animate(dt: number, speed: number): void {
    if (speed > 0) this.walkPhase += dt * speed * 4;

    const swing = speed > 0 ? Math.sin(this.walkPhase) * 0.5 : 0;
    const legs = this.model.legs;
    for (let i = 0; i < legs.length; i++) {
      // 0,3 と 1,2 が対になるように（対角の脚が同じ向きへ出る）
      const sign = i === 0 || i === 3 ? 1 : -1;
      legs[i].rotation.x = swing * sign;
    }

    // 立ち止まっているときは頭をゆっくり上下させる
    this.model.head.rotation.x = speed > 0 ? 0 : Math.sin(this.walkPhase * 0.5) * 0.08;
    if (speed === 0) this.walkPhase += dt;
  }
}
