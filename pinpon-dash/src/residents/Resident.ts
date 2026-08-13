import * as THREE from 'three';
import {
  AVOID_PROBE,
  CATCH_RANGE,
  CHASE_THRESHOLD,
  LOST_GRACE,
  RESIDENT_DOOR_DELAY,
  WANDER_RETARGET,
  WATCH_RATE_FAR,
  WATCH_RATE_NEAR,
  WATCH_GAUGE_MAX,
} from '../core/config';
import type { ColliderSet } from '../physics/Collision';
import { yawFromDirection } from '../town/layout';
import { buildResident, type ResidentModel } from './models/buildResident';
import type { ResidentType } from './residentTypes';

/**
 * 住民の状態（指示書 §9）。
 *
 *   NORMAL     … 家の中。玄関が開くまでの間だけこの状態でいる
 *   SUSPICIOUS … 出てきて周囲を確認している
 *   DETECTED   … プレイヤーを視認。視認ゲージが溜まっていく
 *   CHASE      … 追跡。見えている間は最後に見た位置を更新し続ける
 *   SEARCH     … 見失った。最後に見た場所の周りを捜す
 *   RETURN     … 諦めて家へ帰る。着いたら消える
 */
export type ResidentState = 'NORMAL' | 'SUSPICIOUS' | 'DETECTED' | 'CHASE' | 'SEARCH' | 'RETURN';

/** 追跡は「今いる場所」ではなく「最後に見た場所」へ向かう。角を曲がれば振り切れる。 */
interface Point {
  x: number;
  z: number;
}

export class Resident {
  readonly group = new THREE.Group();
  readonly position = new THREE.Vector3();

  state: ResidentState = 'NORMAL';

  /** 0〜1。1 でゲームオーバー。 */
  gauge = 0;

  /** 一度でも追跡状態に入ったか。まいたときのボーナス判定に使う。 */
  everChased = false;

  /** 家に帰り着いた。ResidentManager がシーンから外す。 */
  finished = false;

  /** 追跡に入った瞬間だけ true。ResidentManager が読んで false に戻す。 */
  chaseStarted = false;

  private readonly model: ResidentModel;

  /** モデルの向き（ラジアン）。移動方向や視線の向きへ、なめらかに追従させる。 */
  private yaw = 0;

  private timer = RESIDENT_DOOR_DELAY;
  private walkPhase = 0;

  /** 今フレームの実際の移動速度。歩きモーションの速さに使う。 */
  private speed = 0;

  /** 追跡に使った合計時間。type.chaseStamina を超えたら息が上がって諦める。 */
  private chaseElapsed = 0;

  private lastSeen: Point | null = null;
  private lostTimer = 0;
  private wanderTarget: Point | null = null;
  private wanderTimer = 0;

  constructor(
    readonly type: ResidentType,
    /** どの家から出てきたか。 */
    readonly houseId: number,
    /** 玄関の前。ここに現れ、諦めたらここへ帰る。 */
    readonly home: Point,
    /** 門を出たところ。様子をうかがう定位置。 */
    readonly post: Point,
    /** 家の正面の向き。出てきたときはこちらを向いている。 */
    front: Point,
  ) {
    this.position.set(home.x, 0, home.z);
    this.yaw = yawFromDirection(front.x, front.z);

    this.model = buildResident(type);
    this.group.add(this.model.group);
    this.group.position.copy(this.position);
    this.group.rotation.y = this.yaw;

    // 玄関が開くまでは姿を見せない
    this.group.visible = false;
  }

  /** プレイヤーを追いかけている最中か（危険度の減衰を止めるのに使う）。 */
  get isChasing(): boolean {
    return this.state === 'CHASE';
  }

  /** 家の前で様子をうかがっている段階か。 */
  get isAlert(): boolean {
    return this.state !== 'NORMAL' && this.state !== 'RETURN';
  }

  /**
   * 1フレーム分の更新。戻り値が true ならプレイヤーを捕まえた。
   */
  update(dt: number, player: THREE.Vector3, colliders: ColliderSet): boolean {
    if (this.state === 'NORMAL') {
      this.timer -= dt;
      if (this.timer > 0) return false;
      this.enterSuspicious();
    }

    const visible = this.canSee(player, colliders);
    this.updateGauge(dt, visible, player);

    switch (this.state) {
      case 'SUSPICIOUS':
        this.updateSuspicious(dt, visible, colliders);
        break;
      case 'DETECTED':
        this.updateDetected(dt, visible, player, colliders);
        break;
      case 'CHASE':
        this.updateChase(dt, visible, player, colliders);
        break;
      case 'SEARCH':
        this.updateSearch(dt, visible, colliders);
        break;
      case 'RETURN':
        this.updateReturn(dt, colliders);
        break;
    }

    this.applyTransform(dt);

    // 捕まえ判定は追跡中だけ。様子見の住民の横をすり抜けても捕まらない。
    if (this.state === 'CHASE') {
      const dx = player.x - this.position.x;
      const dz = player.z - this.position.z;
      if (Math.hypot(dx, dz) <= CATCH_RANGE) return true;
    }
    return false;
  }

  // ── 視界 ───────────────────────────────────────

  /**
   * プレイヤーが見えているか（指示書 §10）。
   *
   * 距離・視野角・遮蔽物の3つで判定する。塀や車の向こうにいるプレイヤーは
   * どれだけ近くても見えない ── これが逃走の基本の仕掛け。
   */
  private canSee(player: THREE.Vector3, colliders: ColliderSet): boolean {
    if (this.state === 'NORMAL' || this.state === 'RETURN') return false;

    const dx = player.x - this.position.x;
    const dz = player.z - this.position.z;
    const distance = Math.hypot(dx, dz);
    if (distance > this.type.viewRange) return false;
    if (distance < 0.001) return true;

    // モデルは +Z が正面
    const forwardX = Math.sin(this.yaw);
    const forwardZ = Math.cos(this.yaw);
    const dot = (dx * forwardX + dz * forwardZ) / distance;
    const halfAngle = (this.type.viewAngle * Math.PI) / 360;
    if (dot < Math.cos(halfAngle)) return false;

    return colliders.canSee(this.position.x, this.position.z, player.x, player.z);
  }

  /** 見られている間は溜まり、視界から外れると減る。近いほど速く溜まる。 */
  private updateGauge(dt: number, visible: boolean, player: THREE.Vector3): void {
    if (visible) {
      // 目の前なら WATCH_RATE_NEAR 倍、視界のふちなら WATCH_RATE_FAR 倍。
      // 遠ければゆっくりしか溜まらないので、走って距離を取る意味が出る。
      const distance = Math.hypot(player.x - this.position.x, player.z - this.position.z);
      const closeness = 1 - Math.min(distance / this.type.viewRange, 1);
      const rate = WATCH_RATE_FAR + (WATCH_RATE_NEAR - WATCH_RATE_FAR) * closeness;
      this.gauge = Math.min(WATCH_GAUGE_MAX, this.gauge + this.type.gaugeUp * rate * dt);
      this.lastSeen = { x: player.x, z: player.z };
      this.lostTimer = 0;
    } else {
      this.gauge = Math.max(0, this.gauge - this.type.gaugeDown * dt);
      this.lostTimer += dt;
    }
  }

  // ── 各状態 ─────────────────────────────────────

  private enterSuspicious(): void {
    this.state = 'SUSPICIOUS';
    this.timer = this.type.suspiciousTime;
    this.group.visible = true;
    this.wanderTarget = null;
  }

  /** 出てきて周囲を見回す。ここで見つからなければ帰る。 */
  private updateSuspicious(dt: number, visible: boolean, colliders: ColliderSet): void {
    if (visible) {
      this.state = 'DETECTED';
      return;
    }

    this.timer -= dt;
    if (this.timer <= 0) {
      this.state = 'RETURN';
      return;
    }

    // まず門の外へ出て、そのあたりをうろうろしながら首を振って確認する。
    // 前庭に立ったままだと塀が邪魔で何も見えないので、必ず外に出る。
    const outside = Math.hypot(this.post.x - this.position.x, this.post.z - this.position.z) < 1.2;
    if (!outside) {
      this.moveTowards(dt, this.post.x, this.post.z, this.type.walkSpeed, colliders);
      return;
    }

    this.wanderAround(dt, this.post, 5, this.type.walkSpeed * 0.7, colliders);
  }

  /**
   * 見つけた。ゲージが CHASE_THRESHOLD を超えるまでは、
   * 「あれっ？」と近づきながら確かめている段階。ここで物陰に入れば助かる。
   */
  private updateDetected(
    dt: number,
    visible: boolean,
    player: THREE.Vector3,
    colliders: ColliderSet,
  ): void {
    if (!visible) {
      // 見失った。まだ確信が無いので、様子見に戻る
      this.state = 'SUSPICIOUS';
      this.timer = Math.max(this.timer, this.type.suspiciousTime * 0.6);
      return;
    }

    this.faceTowards(dt, player.x, player.z, 8);
    this.moveTowards(dt, player.x, player.z, this.type.walkSpeed, colliders);

    if (this.gauge >= CHASE_THRESHOLD) {
      this.startChase();
    }
  }

  private startChase(): void {
    if (this.state !== 'CHASE') this.chaseStarted = true;
    this.state = 'CHASE';
    this.everChased = true;
    this.timer = this.type.chaseTime;
  }

  /**
   * 追跡。見えている間は行き先を更新し続けるが、見失ったあとは
   * 「最後に見た位置」へ向かう。まっすぐプレイヤーを追わないのが肝で、
   * だから角を曲がると振り切れる（指示書 §9, §11）。
   */
  private updateChase(
    dt: number,
    visible: boolean,
    player: THREE.Vector3,
    colliders: ColliderSet,
  ): void {
    // 走った分だけ息が切れる。見えていようがいまいが減る一方で、
    // 使い切ったらその場で諦める（指示書 §8 の「一定時間で追跡を諦める」）。
    this.chaseElapsed += dt;
    if (this.chaseElapsed >= this.type.chaseStamina) {
      this.state = 'RETURN';
      return;
    }

    if (visible) {
      // 見えている限り追い続ける。見失ってからのタイマーは満タンに戻しておく
      this.timer = this.type.chaseTime;
      this.moveTowards(dt, player.x, player.z, this.type.chaseSpeed, colliders);
      return;
    }

    this.timer -= dt;

    const target = this.lastSeen;
    if (target) {
      this.moveTowards(dt, target.x, target.z, this.type.chaseSpeed, colliders);
    }

    // 最後に見た位置へ走り、着いたら（または時間切れで）そのあたりを捜す
    const reached =
      target !== null && Math.hypot(target.x - this.position.x, target.z - this.position.z) < 1.2;
    if (this.timer <= 0 || (this.lostTimer > LOST_GRACE && reached)) {
      this.state = 'SEARCH';
      this.timer = this.type.searchTime;
      this.wanderTarget = null;
    }
  }

  /** 最後に見た場所の周りを捜す。危険な住民ほど長く粘る。 */
  private updateSearch(dt: number, visible: boolean, colliders: ColliderSet): void {
    if (visible) {
      this.startChase();
      return;
    }

    this.timer -= dt;
    if (this.timer <= 0) {
      this.state = 'RETURN';
      return;
    }

    const center = this.lastSeen ?? this.home;
    this.wanderAround(dt, center, 6, this.type.walkSpeed, colliders);
  }

  /** 諦めて帰る。帰り道ではもう周りを見ていない。 */
  private updateReturn(dt: number, colliders: ColliderSet): void {
    this.moveTowards(dt, this.home.x, this.home.z, this.type.walkSpeed, colliders);

    const distance = Math.hypot(this.home.x - this.position.x, this.home.z - this.position.z);
    if (distance < 1.0) this.finished = true;
  }

  // ── 移動 ───────────────────────────────────────

  /** 指定の点の周りを、行き先を選び直しながらうろつく。 */
  private wanderAround(
    dt: number,
    center: Point,
    radius: number,
    speed: number,
    colliders: ColliderSet,
  ): void {
    this.wanderTimer -= dt;

    const arrived =
      this.wanderTarget !== null &&
      Math.hypot(this.wanderTarget.x - this.position.x, this.wanderTarget.z - this.position.z) < 1;

    // 着いたか、しばらく粘っても着けなければ選び直す（塀の裏など、行けない先もある）
    if (this.wanderTarget === null || arrived || this.wanderTimer <= 0) {
      const angle = Math.random() * Math.PI * 2;
      const distance = radius * (0.4 + Math.random() * 0.6);
      this.wanderTarget = {
        x: center.x + Math.sin(angle) * distance,
        z: center.z + Math.cos(angle) * distance,
      };
      this.wanderTimer = WANDER_RETARGET;
    }

    this.moveTowards(dt, this.wanderTarget.x, this.wanderTarget.z, speed, colliders);
  }

  /**
   * 目標へ向かって進む。経路探索は持たない代わりに、
   * 正面が塞がっていたら左右へ角度をずらして、抜けられる向きを探す。
   *
   * 住宅街は道が格子状なので、これだけで角も曲がれるし塀も回り込める。
   * 完全ではないが、プレイヤーから見て「壁に沿って回り込んできた」ように見える。
   */
  private moveTowards(
    dt: number,
    targetX: number,
    targetZ: number,
    speed: number,
    colliders: ColliderSet,
  ): void {
    const dx = targetX - this.position.x;
    const dz = targetZ - this.position.z;
    const distance = Math.hypot(dx, dz);
    if (distance < 0.05) {
      this.speed = 0;
      return;
    }

    const baseAngle = Math.atan2(dx, dz);
    let chosen = baseAngle;

    // 0° → ±30° → ±60° → ±90° の順に、空いている向きを探す
    for (const offset of [0, 0.52, -0.52, 1.05, -1.05, 1.57, -1.57]) {
      const angle = baseAngle + offset;
      if (this.probe(angle, colliders)) {
        chosen = angle;
        break;
      }
    }

    const stepX = Math.sin(chosen) * speed * dt;
    const stepZ = Math.cos(chosen) * speed * dt;
    const resolved = colliders.resolveCircle(
      this.position.x + stepX,
      this.position.z + stepZ,
      this.type.radius,
    );

    // 実際に動けた距離。押し戻されていれば歩行モーションも止まる
    this.speed = Math.hypot(resolved.x - this.position.x, resolved.z - this.position.z) / dt;
    this.position.x = resolved.x;
    this.position.z = resolved.z;

    this.faceTowards(dt, targetX, targetZ, 6, chosen);
  }

  /** その向きへ AVOID_PROBE 進んだ先に立てるか。手前も見て、角の引っかかりを防ぐ。 */
  private probe(angle: number, colliders: ColliderSet): boolean {
    const sin = Math.sin(angle);
    const cos = Math.cos(angle);
    for (const reach of [AVOID_PROBE * 0.5, AVOID_PROBE]) {
      const x = this.position.x + sin * reach;
      const z = this.position.z + cos * reach;
      if (!colliders.free(x, z, this.type.radius)) return false;
    }
    return true;
  }

  /** 体の向きをなめらかに回す。急に振り向くと機械っぽく見える。 */
  private faceTowards(
    dt: number,
    targetX: number,
    targetZ: number,
    rate: number,
    angleOverride?: number,
  ): void {
    const target =
      angleOverride ?? Math.atan2(targetX - this.position.x, targetZ - this.position.z);

    // -π〜π に畳んでから近い側へ回す
    let delta = target - this.yaw;
    while (delta > Math.PI) delta -= Math.PI * 2;
    while (delta < -Math.PI) delta += Math.PI * 2;

    this.yaw += delta * Math.min(dt * rate, 1);
  }

  // ── 見た目 ─────────────────────────────────────

  private applyTransform(dt: number): void {
    this.group.position.set(this.position.x, this.position.y, this.position.z);
    this.group.rotation.y = this.yaw;

    // 速いほど大きく速く手足を振る。走っているときは腕も大きく回る
    this.walkPhase += dt * (2 + this.speed * 3.2);
    const swing = Math.min(this.speed / 3, 1.2);

    const legSwing = Math.sin(this.walkPhase) * 0.75 * swing;
    this.model.legs[0].rotation.x = legSwing;
    this.model.legs[1].rotation.x = -legSwing;

    const armSwing = Math.sin(this.walkPhase) * 0.6 * swing;
    this.model.arms[0].rotation.x = -armSwing;
    this.model.arms[1].rotation.x = armSwing;

    if (this.state === 'CHASE') {
      // 追いかけるときは両腕を前に突き出す。遠くからでも「追われている」と分かる
      this.model.arms[0].rotation.x = -1.5 + Math.sin(this.walkPhase * 2) * 0.25;
      this.model.arms[1].rotation.x = -1.5 - Math.sin(this.walkPhase * 2) * 0.25;
      this.group.position.y = Math.abs(Math.sin(this.walkPhase)) * 0.07;
    } else {
      this.group.position.y = 0;
    }

    if (this.state === 'SUSPICIOUS' || this.state === 'SEARCH') {
      // きょろきょろ。首だけ左右に振る
      this.model.head.rotation.y = Math.sin(this.walkPhase * 0.9) * 0.6;
    } else {
      this.model.head.rotation.y = 0;
    }
  }

  dispose(): void {
    this.model.dispose();
  }
}
