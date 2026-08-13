import * as THREE from 'three';
import { PATROL_BACKTRACK } from '../core/config';
import { createRandom, pick } from '../core/rng';
import { ColliderSet } from '../physics/Collision';
import { MeshBuilder } from './MeshBuilder';
import * as C from './palette';
import { CELL, NEIGHBORS, TownGrid, yawFromDirection } from './layout';

/** 街の見た目を決めるシード。変えると小物の置き方だけが変わる。 */
const TOWN_SEED = 20260813;

/** 敷地の1辺。区画（CELL）より少し小さくして、道路との間に隙間を作る。 */
const LOT = 9.4;

/** ブロック塀の高さと厚み。人の背より高いので、しゃがまなくても視線が切れる。 */
const WALL_HEIGHT = 1.7;
const WALL_THICKNESS = 0.3;

/** 門の開口部の幅。ここから住民が出てくるし、プレイヤーも入り込める。 */
const GATE_WIDTH = 3.2;

/** 家の本体。敷地の奥に寄せて、門との間に前庭を残す。 */
const HOUSE_WIDTH = 6.4;
const HOUSE_DEPTH = 5.6;
const HOUSE_HEIGHT = 5.4;
const ROOF_HEIGHT = 1.9;

/**
 * 玄関から門までの距離（前庭の奥行き）。
 *
 * ここがゲームの手触りを決める。住民は玄関から出て門へ歩いてくるので、
 * この距離がそのまま「鳴らしてから逃げ出すまでの猶予」になる。
 * 0 にすると、鳴らした指の真横に住民が湧いて何もできずに捕まる。
 */
const FRONT_YARD = 3.4;

/** インターホンの高さ。 */
const DOORBELL_HEIGHT = 1.25;

/** 地図の升目。徘徊の行き先はこの単位で決める。 */
export interface Cell {
  readonly col: number;
  readonly row: number;
}

export interface House {
  readonly id: number;
  /** 敷地の中心。 */
  readonly center: { x: number; z: number };
  /** 正面（道路側）を向いた単位ベクトル。 */
  readonly front: { x: number; z: number };
  /** 玄関の前。住民はここに現れ、ここへ帰る。 */
  readonly door: { x: number; z: number };
  /** 門の中心。塀の開口部。 */
  readonly gate: { x: number; z: number };
  /** 門を出たところ。住民が様子をうかがう定位置。 */
  readonly post: { x: number; z: number };
  /** インターホンのパネルの位置。プレイヤーとの距離はここで測る。 */
  readonly doorbell: { x: number; y: number; z: number };
  /** インターホンのボタン（近づくと光る）。 */
  readonly button: THREE.Mesh;
}

/**
 * 街そのもの。地図（layout.ts）から見た目・当たり判定・家の一覧を組み立てる。
 *
 * 出来上がったあとは動かない。住民とプレイヤーだけが動く。
 */
export class Town {
  readonly group = new THREE.Group();
  readonly colliders = new ColliderSet();
  readonly houses: House[] = [];
  readonly grid: TownGrid;

  /** プレイヤーの開始位置。 */
  readonly spawn: { x: number; z: number };

  private readonly builder = new MeshBuilder();
  private readonly random = createRandom(TOWN_SEED);
  private readonly poles: { x: number; z: number; col: number; row: number }[] = [];

  constructor() {
    this.grid = new TownGrid();

    this.buildGround();
    for (const cell of this.grid.each()) {
      switch (cell.kind) {
        case 'wall':
          this.buildOuterWall(cell.col, cell.row);
          break;
        case 'road':
          this.buildRoad(cell.col, cell.row);
          break;
        case 'alley':
          this.buildAlley(cell.col, cell.row);
          break;
        case 'house':
          this.buildHouse(cell.col, cell.row);
          break;
        case 'park':
          this.buildPark(cell.col, cell.row);
          break;
        case 'vacant':
          this.buildVacant(cell.col, cell.row);
          break;
        case 'parking':
          this.buildParking(cell.col, cell.row);
          break;
      }
    }
    this.buildWires();

    this.group.add(this.builder.build());

    // 開始位置は街のまんなかの十字路。どちらへ走っても道が続く。
    this.spawn = this.grid.center(6, 8);
  }

  /** 家がいくつあるか（デバッグと README 用）。 */
  get houseCount(): number {
    return this.houses.length;
  }

  // ── 徘徊のための道案内 ───────────────────────────

  /**
   * その座標がどの区画かを返す。街の外なら null。
   */
  cellAt(x: number, z: number): Cell | null {
    const col = Math.round(x / CELL + (this.grid.width - 1) / 2);
    const row = Math.round(z / CELL + (this.grid.depth - 1) / 2);
    if (col < 0 || row < 0 || col >= this.grid.width || row >= this.grid.depth) return null;
    return { col, row };
  }

  /**
   * 徘徊する住民の、次の行き先（追加仕様 §10）。
   *
   * いまいる区画から、通れる隣の区画をひとつ選んで、その中心を返す。
   * **隣の区画しか選ばない**のがこの実装の肝で、
   *
   *   ・必ずたどり着ける（経路探索が要らない）
   *   ・道と路地の上だけを歩く（家や塀の中を突っ切らない）
   *   ・区画をまたぐたびに選び直すので、街全体へ広がっていく
   *
   * が同時に満たせる。来た道へ引き返す確率は PATROL_BACKTRACK で決める
   * （行き止まりでは引き返すしかないので、そこだけは無条件で許す）。
   */
  patrolStep(from: Cell, previous: Cell | null): { x: number; z: number } | null {
    const options: Cell[] = [];
    let back: Cell | null = null;

    for (const neighbor of NEIGHBORS) {
      const col = from.col + neighbor.dcol;
      const row = from.row + neighbor.drow;
      if (!this.grid.walkable(col, row)) continue;

      if (previous && previous.col === col && previous.row === row) back = { col, row };
      else options.push({ col, row });
    }

    // 行き止まりなら引き返すしかない
    const pool = options.length === 0 || (back && Math.random() < PATROL_BACKTRACK) ? [back!] : options;
    const cell = pool[Math.floor(Math.random() * pool.length)];
    if (!cell) return null;

    return this.grid.center(cell.col, cell.row);
  }

  // ── 地面 ───────────────────────────────────────

  private buildGround(): void {
    const width = this.grid.width * CELL;
    const depth = this.grid.depth * CELL;
    // 全体を土の色で敷いておき、その上に道路や芝を重ねる。
    this.builder.plane(0, -0.02, 0, width + 40, depth + 40, C.DIRT);
  }

  private buildOuterWall(col: number, row: number): void {
    // 地図の外周と、通れない塊。街の外へ出られないようにするだけの存在なので、
    // 見た目は「向こう側にも家並みが続いている」ふうの箱にしておく。
    const { x, z } = this.grid.center(col, row);
    const height = 7 + this.random() * 4;
    this.builder.box(x, 0, z, CELL, height, CELL, pick(this.random, C.HOUSE_WALLS));
    this.builder.roof(x, height, z, CELL, 2.2, CELL, pick(this.random, C.HOUSE_ROOFS));
    this.colliders.addBox(x, z, CELL, CELL);
  }

  // ── 道 ─────────────────────────────────────────

  private buildRoad(col: number, row: number): void {
    const { x, z } = this.grid.center(col, row);
    this.builder.plane(x, 0, z, CELL, CELL, C.ROAD);

    // 交差点でない直線の道にだけ、白線を1本引く。方角の手がかりになる。
    const horizontal = this.grid.walkable(col - 1, row) && this.grid.walkable(col + 1, row);
    const vertical = this.grid.walkable(col, row - 1) && this.grid.walkable(col, row + 1);
    if (horizontal && !vertical) this.builder.plane(x, 0.01, z, CELL, 0.18, C.ROAD_LINE);
    if (vertical && !horizontal) this.builder.plane(x, 0.01, z, 0.18, CELL, C.ROAD_LINE);

    this.decorateRoad(col, row, x, z);
  }

  /**
   * 道端の小物。すべて決定論で置く。
   * 電柱と自販機は視線を切る「盾」になるので、置き場所はゲーム性に直結する。
   */
  private decorateRoad(col: number, row: number, x: number, z: number): void {
    const roll = this.random();

    // 電柱は道の隅に。電線を張るので位置を覚えておく。
    if (roll < 0.34) {
      const px = x + (this.random() < 0.5 ? -1 : 1) * (CELL / 2 - 0.7);
      const pz = z + (this.random() < 0.5 ? -1 : 1) * (CELL / 2 - 0.7);
      this.builder.cylinder(px, 0, pz, 0.17, 7.2, C.POLE, 6);
      this.builder.box(px, 6.2, pz, 1.9, 0.12, 0.12, C.POLE);
      // 細いので視線は通す。隠れ場所にはならないが、走る邪魔にはなる。
      this.colliders.addBox(px, pz, 0.5, 0.5, { opaque: false });
      this.poles.push({ x: px, z: pz, col, row });
      return;
    }

    // 自動販売機。夜でも光っていそうな赤。曲がり角に置くと格好の遮蔽物になる。
    if (roll < 0.44) {
      const side = this.pickRoadside(col, row);
      if (side) {
        const yaw = yawFromDirection(-side.dx, -side.dz);
        const vx = x + side.dx * (CELL / 2 - 0.9);
        const vz = z + side.dz * (CELL / 2 - 0.9);
        this.builder.box(vx, 0, vz, 1.2, 1.9, 0.8, C.VENDING, yaw);
        this.builder.box(vx - side.dx * 0.45, 0.55, vz - side.dz * 0.45, 0.9, 1.1, 0.05, C.VENDING_PANEL, yaw);
        this.colliders.addBox(vx, vz, 1.4, 1.4);
      }
      return;
    }

    // 郵便ポスト。小さいので視線は通る。
    if (roll < 0.5) {
      const side = this.pickRoadside(col, row);
      if (side) {
        const px = x + side.dx * (CELL / 2 - 0.8);
        const pz = z + side.dz * (CELL / 2 - 0.8);
        this.builder.cylinder(px, 0, pz, 0.28, 1.35, C.POST_BOX, 8);
        this.builder.cylinder(px, 1.35, pz, 0.32, 0.16, C.POST_BOX, 8);
        this.colliders.addBox(px, pz, 0.7, 0.7, { opaque: false });
      }
    }
  }

  /** 道路区画のうち、家や壁に接している辺を1つ返す（小物を置く向き）。 */
  private pickRoadside(col: number, row: number): { dx: number; dz: number } | null {
    const sides = NEIGHBORS.filter((n) => !this.grid.walkable(col + n.dcol, row + n.drow));
    if (sides.length === 0) return null;
    const side = pick(this.random, sides);
    return { dx: side.dcol, dz: side.drow };
  }

  /** 電柱どうしを電線でつなぐ。空を見上げたときの「日本の住宅街」らしさ。 */
  private buildWires(): void {
    for (const pole of this.poles) {
      for (const other of this.poles) {
        // 同じ列 or 同じ行で、1〜2区画だけ離れている相手と結ぶ（重複を避けて片方向）
        const sameCol = pole.col === other.col && other.row > pole.row && other.row - pole.row <= 2;
        const sameRow = pole.row === other.row && other.col > pole.col && other.col - pole.col <= 2;
        if (!sameCol && !sameRow) continue;

        const dx = other.x - pole.x;
        const dz = other.z - pole.z;
        const length = Math.hypot(dx, dz);
        const midX = (pole.x + other.x) / 2;
        const midZ = (pole.z + other.z) / 2;
        for (const offset of [-0.55, 0, 0.55]) {
          const yaw = yawFromDirection(dx / length, dz / length);
          this.builder.box(
            midX + Math.cos(yaw) * offset,
            6.35,
            midZ - Math.sin(yaw) * offset,
            0.05,
            0.05,
            length,
            C.WIRE,
            yaw,
          );
        }
      }
    }
  }

  private buildAlley(col: number, row: number): void {
    const { x, z } = this.grid.center(col, row);
    this.builder.plane(x, 0, z, CELL, CELL, C.ALLEY);

    // 通り抜けの向きに合わせて、両側に塀を立てて細くする。
    const vertical = this.grid.walkable(col, row - 1) || this.grid.walkable(col, row + 1);
    const half = 1.9; // 通路の半幅。狭くするほど「路地」らしくなる
    const side = CELL / 2;

    for (const sign of [-1, 1]) {
      if (vertical) {
        const wx = x + sign * (half + (side - half) / 2);
        this.builder.box(wx, 0, z, side - half, WALL_HEIGHT, CELL, C.BLOCK_WALL);
        this.builder.box(wx, WALL_HEIGHT, z, side - half, 0.12, CELL, C.BLOCK_WALL_CAP);
        this.colliders.addBox(wx, z, side - half, CELL);
      } else {
        const wz = z + sign * (half + (side - half) / 2);
        this.builder.box(x, 0, wz, CELL, WALL_HEIGHT, side - half, C.BLOCK_WALL);
        this.builder.box(x, WALL_HEIGHT, wz, CELL, 0.12, side - half, C.BLOCK_WALL_CAP);
        this.colliders.addBox(x, wz, CELL, side - half);
      }
    }
  }

  // ── 家 ─────────────────────────────────────────

  private buildHouse(col: number, row: number): void {
    const center = this.grid.center(col, row);

    // 道路に面した辺を探す。NEIGHBORS の順序が「南向きの玄関を優先」になっている。
    const facing = NEIGHBORS.find((n) => this.grid.walkable(col + n.dcol, row + n.drow));
    if (!facing) {
      throw new Error(`道路に面していない家があります: 地図の ${row} 行 ${col} 列`);
    }

    const front = { x: facing.dcol, z: facing.drow };
    const yaw = yawFromDirection(front.x, front.z);
    // 正面を向いたときの「右手」。塀を分割したり門柱を置いたりするのに使う。
    const side = { x: front.z, z: -front.x };

    const wallColor = pick(this.random, C.HOUSE_WALLS);
    const roofColor = pick(this.random, C.HOUSE_ROOFS);

    // 家本体は敷地の奥へ。門との間に FRONT_YARD ぶんの前庭ができる。
    const setback = HOUSE_DEPTH / 2 - (LOT / 2 - FRONT_YARD);
    const hx = center.x - front.x * setback;
    const hz = center.z - front.z * setback;

    this.builder.box(hx, 0, hz, HOUSE_WIDTH, HOUSE_HEIGHT, HOUSE_DEPTH, wallColor, yaw);
    this.builder.roof(hx, HOUSE_HEIGHT, hz, HOUSE_WIDTH + 0.7, ROOF_HEIGHT, HOUSE_DEPTH + 0.7, roofColor, yaw);
    this.colliders.addBox(hx, hz, this.spanX(yaw, HOUSE_WIDTH, HOUSE_DEPTH), this.spanZ(yaw, HOUSE_WIDTH, HOUSE_DEPTH));

    // 玄関と窓。正面の壁のすぐ手前に薄い板を貼るだけ。
    const faceX = hx + front.x * (HOUSE_DEPTH / 2 + 0.03);
    const faceZ = hz + front.z * (HOUSE_DEPTH / 2 + 0.03);
    this.builder.box(faceX + side.x * 1.4, 0, faceZ + side.z * 1.4, 1.3, 2.1, 0.08, C.DOOR, yaw);
    this.builder.box(faceX - side.x * 1.6, 1.1, faceZ - side.z * 1.6, 1.9, 1.3, 0.08, C.WINDOW, yaw);
    this.builder.box(faceX - side.x * 1.6, 3.6, faceZ - side.z * 1.6, 1.9, 1.2, 0.08, C.WINDOW, yaw);
    this.builder.box(faceX + side.x * 1.4, 3.6, faceZ + side.z * 1.4, 1.4, 1.2, 0.08, C.WINDOW, yaw);

    // 敷地を囲むブロック塀。道路に面した側だけに立てる（家どうしの間は空ける）。
    for (const neighbor of NEIGHBORS) {
      if (!this.grid.walkable(col + neighbor.dcol, row + neighbor.drow)) continue;
      const isFront = neighbor === facing;
      this.buildLotWall(center, neighbor.dcol, neighbor.drow, isFront);
    }

    const gate = {
      x: center.x + front.x * (LOT / 2),
      z: center.z + front.z * (LOT / 2),
    };

    // 門柱とインターホン。門の開口部の脇に立てる。
    const postOffset = GATE_WIDTH / 2 + 0.25;
    const postX = gate.x + side.x * postOffset;
    const postZ = gate.z + side.z * postOffset;
    this.builder.box(postX, 0, postZ, 0.5, 1.55, 0.5, C.GATE_POST, yaw);
    this.builder.box(postX, 1.55, postZ, 0.62, 0.1, 0.62, C.BLOCK_WALL_CAP, yaw);
    this.colliders.addBox(postX, postZ, 0.6, 0.6, { opaque: false });

    // インターホンのパネル（門柱の道路側の面）
    const plateX = postX + front.x * 0.28;
    const plateZ = postZ + front.z * 0.28;
    this.builder.box(plateX, DOORBELL_HEIGHT - 0.15, plateZ, 0.3, 0.4, 0.04, C.DOORBELL_PLATE, yaw);

    // ボタンだけは別メッシュ。近づいたときに光らせたいので結合しない。
    const button = new THREE.Mesh(
      new THREE.BoxGeometry(0.13, 0.13, 0.06),
      new THREE.MeshLambertMaterial({ color: C.DOORBELL_BUTTON }),
    );
    button.position.set(plateX + front.x * 0.03, DOORBELL_HEIGHT, plateZ + front.z * 0.03);
    button.rotation.y = yaw;
    this.group.add(button);

    // 前庭の植木。低いので視線は通すが、走る邪魔にはなる。
    if (this.random() < 0.6) {
      const px = gate.x - front.x * 1.6 - side.x * 2.6;
      const pz = gate.z - front.z * 1.6 - side.z * 2.6;
      this.builder.box(px, 0, pz, 1.3, 0.9, 1.3, C.HEDGE, yaw);
      this.colliders.addBox(px, pz, 1.3, 1.3, { opaque: false });
    }

    this.houses.push({
      id: this.houses.length,
      center,
      front,
      // 玄関の板の少し手前。ここから住民が出てくる
      door: {
        x: faceX + front.x * 0.7 + side.x * 1.4,
        z: faceZ + front.z * 0.7 + side.z * 1.4,
      },
      gate,
      // 門を出て道路に一歩。様子をうかがうのはここ
      post: { x: gate.x + front.x * 1.6, z: gate.z + front.z * 1.6 },
      doorbell: { x: plateX, y: DOORBELL_HEIGHT, z: plateZ },
      button,
    });
  }

  /**
   * 敷地の1辺にブロック塀を立てる。正面の辺だけは門の分だけ開ける。
   */
  private buildLotWall(
    center: { x: number; z: number },
    dcol: number,
    drow: number,
    isFront: boolean,
  ): void {
    const wallX = center.x + dcol * (LOT / 2);
    const wallZ = center.z + drow * (LOT / 2);
    const alongX = dcol === 0; // 辺が X 方向に伸びるのは、南北の辺

    const place = (offset: number, length: number): void => {
      const x = wallX + (alongX ? offset : 0);
      const z = wallZ + (alongX ? 0 : offset);
      const width = alongX ? length : WALL_THICKNESS;
      const depth = alongX ? WALL_THICKNESS : length;
      this.builder.box(x, 0, z, width, WALL_HEIGHT, depth, C.BLOCK_WALL);
      this.builder.box(x, WALL_HEIGHT, z, width + 0.1, 0.12, depth + 0.1, C.BLOCK_WALL_CAP);
      this.colliders.addBox(x, z, width, depth);
    };

    if (!isFront) {
      place(0, LOT);
      return;
    }

    // 門の開口部を残して左右に分ける
    const segment = (LOT - GATE_WIDTH) / 2;
    for (const sign of [-1, 1]) {
      place(sign * (GATE_WIDTH / 2 + segment / 2), segment);
    }
  }

  /** 回転した箱が X 方向に占める幅。当たり判定は軸に沿った箱で近似する。 */
  private spanX(yaw: number, width: number, depth: number): number {
    return Math.abs(Math.cos(yaw)) > 0.5 ? width : depth;
  }

  private spanZ(yaw: number, width: number, depth: number): number {
    return Math.abs(Math.cos(yaw)) > 0.5 ? depth : width;
  }

  // ── 公園・空き地・駐車場 ─────────────────────────

  private buildPark(col: number, row: number): void {
    const { x, z } = this.grid.center(col, row);
    this.builder.plane(x, 0, z, CELL, CELL, C.GRASS);

    // 木は視線を切る。公園を突っ切って逃げるときの命綱になる。
    const trees = 1 + Math.floor(this.random() * 2);
    for (let i = 0; i < trees; i++) {
      const tx = x + (this.random() - 0.5) * (CELL - 3);
      const tz = z + (this.random() - 0.5) * (CELL - 3);
      const height = 2.6 + this.random() * 1.4;
      this.builder.cylinder(tx, 0, tz, 0.28, height, C.TREE_TRUNK, 6);
      this.builder.box(tx, height, tz, 3.2, 2.4, 3.2, C.TREE_LEAF);
      this.builder.box(tx, height + 2.0, tz, 2.2, 1.4, 2.2, C.TREE_LEAF);
      this.colliders.addBox(tx, tz, 1.5, 1.5);
    }

    if (this.random() < 0.5) {
      const bx = x + (this.random() - 0.5) * 4;
      const bz = z + (this.random() - 0.5) * 4;
      this.builder.box(bx, 0.42, bz, 2.0, 0.12, 0.6, C.BENCH);
      this.builder.box(bx, 0, bz - 0.22, 0.14, 0.42, 0.14, C.BENCH);
      this.builder.box(bx, 0, bz + 0.22, 0.14, 0.42, 0.14, C.BENCH);
      this.colliders.addBox(bx, bz, 2.0, 0.7, { opaque: false });
    }

    if (this.random() < 0.4) {
      this.builder.plane(x + 2.5, 0.01, z + 2.5, 3.4, 3.4, C.SAND);
    }
  }

  private buildVacant(col: number, row: number): void {
    const { x, z } = this.grid.center(col, row);
    this.builder.plane(x, 0, z, CELL, CELL, C.DIRT);

    // 空き地は見晴らしがよく、渡り切るまで隠れられない。土管だけが盾になる。
    if (this.random() < 0.7) {
      const px = x + (this.random() - 0.5) * 4;
      const pz = z + (this.random() - 0.5) * 4;
      const yaw = this.random() < 0.5 ? 0 : Math.PI / 2;
      // 2本並べて上に1本。積み方は昔の空き地の定番。
      for (const [offset, height] of [
        [-0.85, 0],
        [0.85, 0],
        [0, 1.6],
      ] as const) {
        const ox = px + Math.cos(yaw) * offset;
        const oz = pz - Math.sin(yaw) * offset;
        this.builder.tube(ox, height, oz, 0.8, 2.2, C.PIPE, yaw);
      }
      const across = 3.4;
      const along = 2.4;
      this.colliders.addBox(px, pz, yaw === 0 ? across : along, yaw === 0 ? along : across);
    }

    // ぐるりと簡易フェンス。抜けられるのは道路に面した辺だけ。
    for (const neighbor of NEIGHBORS) {
      if (this.grid.walkable(col + neighbor.dcol, row + neighbor.drow)) continue;
      const fx = x + neighbor.dcol * (CELL / 2 - 0.15);
      const fz = z + neighbor.drow * (CELL / 2 - 0.15);
      const alongX = neighbor.dcol === 0;
      this.builder.box(fx, 0, fz, alongX ? CELL : 0.1, 1.3, alongX ? 0.1 : CELL, C.FENCE);
    }
  }

  private buildParking(col: number, row: number): void {
    const { x, z } = this.grid.center(col, row);
    this.builder.plane(x, 0, z, CELL, CELL, C.SIDEWALK);

    // 白い枠線
    for (const offset of [-3, 0, 3]) {
      this.builder.plane(x + offset, 0.01, z, 0.12, 5, C.ROAD_LINE);
    }

    const cars = 1 + Math.floor(this.random() * 2);
    for (let i = 0; i < cars; i++) {
      const cx = x + (i === 0 ? -1.5 : 1.5);
      this.buildCar(cx, z, 0);
    }
  }

  /** デフォルメした車。箱2つとタイヤ4つ。視線は通さない。 */
  private buildCar(x: number, z: number, yaw: number): void {
    const body = pick(this.random, C.CAR_BODIES);
    this.builder.box(x, 0.35, z, 1.8, 0.75, 4.0, body, yaw);
    this.builder.box(x, 1.1, z - 0.2, 1.6, 0.7, 2.0, C.CAR_GLASS, yaw);
    for (const dx of [-0.82, 0.82]) {
      for (const dz of [-1.35, 1.35]) {
        const wx = x + Math.cos(yaw) * dx + Math.sin(yaw) * dz;
        const wz = z - Math.sin(yaw) * dx + Math.cos(yaw) * dz;
        this.builder.cylinder(wx, 0, wz, 0.35, 0.3, C.CAR_TIRE, 8);
      }
    }
    this.colliders.addBox(x, z, 2.0, 4.2);
  }
}
