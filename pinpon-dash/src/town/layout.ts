/**
 * 街の間取り。文字を並べただけの地図で、ここを書き換えると街が変わる。
 *
 * 1文字 = 1区画（CELL メートル四方）。上が北（-Z）、左が西（-X）。
 *
 *   x  通れない壁（外周と、大きな建物）
 *   .  道路
 *   ,  路地（両側に塀が立って細くなる。曲がると視線を切りやすい）
 *   h  一戸建て。道路に面した側に門・インターホン・玄関が付く
 *   p  公園（木とベンチ。走り抜けられる）
 *   v  空き地（土。遮蔽物が少なく、渡るのは危険）
 *   k  駐車場（車が並ぶ。車は視線を遮る）
 *
 * 家（h）は必ず1つ以上の通れる区画に接していること。接していないと
 * 門を出す向きが決まらず、TownBuilder が例外を投げる。
 *
 * 逃走ゲームなので、行き止まりと回り込める輪（ループ）を意図的に混ぜてある。
 * 一本道にすると「速い方が勝つ」だけのゲームになってしまう。
 */

/** 1区画の1辺（メートル）。 */
export const CELL = 10;

export const TOWN_MAP: readonly string[] = [
  'xxxxxxxxxxxxxx',
  'xhh.hhh.hh.hhx',
  'x............x',
  'x.hh.hh,.hh..x',
  'x.hh.hh,.hh..x',
  'x......,.....x',
  'x.pp.hh.hh.k.x',
  'x.pp.hh.hh.k.x',
  'x............x',
  'x.hh,vv.hh.hhx',
  'x.hh,vv.hh.hhx',
  'x............x',
  'xhh.h,h.hh.hhx',
  'xxxxxxxxxxxxxx',
];

export type CellKind = 'wall' | 'road' | 'alley' | 'house' | 'park' | 'vacant' | 'parking';

const KIND_BY_CHAR: Readonly<Record<string, CellKind>> = {
  x: 'wall',
  '.': 'road',
  ',': 'alley',
  h: 'house',
  p: 'park',
  v: 'vacant',
  k: 'parking',
};

/** 通り抜けられる区画かどうか（家と壁だけが通れない）。 */
export const isWalkable = (kind: CellKind): boolean => kind !== 'wall' && kind !== 'house';

/** 地図の格子。行 = Z方向、列 = X方向。 */
export class TownGrid {
  readonly width: number;
  readonly depth: number;
  private readonly cells: CellKind[];

  constructor(map: readonly string[] = TOWN_MAP) {
    this.depth = map.length;
    this.width = map[0]?.length ?? 0;
    this.cells = [];

    for (let row = 0; row < this.depth; row++) {
      const line = map[row];
      if (line.length !== this.width) {
        throw new Error(`地図の ${row} 行目の長さが違います（${line.length} / ${this.width}）`);
      }
      for (const char of line) {
        const kind = KIND_BY_CHAR[char];
        if (!kind) throw new Error(`地図に未定義の文字があります: ${char}`);
        this.cells.push(kind);
      }
    }
  }

  /** 範囲外は壁として扱う。街の外へ出ようとしても押し返される。 */
  at(col: number, row: number): CellKind {
    if (col < 0 || row < 0 || col >= this.width || row >= this.depth) return 'wall';
    return this.cells[row * this.width + col];
  }

  walkable(col: number, row: number): boolean {
    return isWalkable(this.at(col, row));
  }

  /** 区画の中心のワールド座標。地図の中心が原点になるようずらす。 */
  center(col: number, row: number): { x: number; z: number } {
    return {
      x: (col - (this.width - 1) / 2) * CELL,
      z: (row - (this.depth - 1) / 2) * CELL,
    };
  }

  /** 全区画を順に。 */
  *each(): Generator<{ col: number; row: number; kind: CellKind }> {
    for (let row = 0; row < this.depth; row++) {
      for (let col = 0; col < this.width; col++) {
        yield { col, row, kind: this.at(col, row) };
      }
    }
  }
}

/**
 * 4近傍。並び順がそのまま「門をどちら向きに付けるか」の優先度になる。
 * 南向きの玄関を優先しているのは、日本の住宅街らしく見えるから。
 */
export const NEIGHBORS: readonly { dcol: number; drow: number }[] = [
  { dcol: 0, drow: 1 }, // 南（+Z）
  { dcol: 1, drow: 0 }, // 東（+X）
  { dcol: -1, drow: 0 }, // 西（-X）
  { dcol: 0, drow: -1 }, // 北（-Z）
];

/**
 * 向き（単位ベクトル）を Three.js の Y 回転に直す。
 * このゲームのモデルはすべて +Z を正面として組み立てている。
 */
export const yawFromDirection = (dx: number, dz: number): number => Math.atan2(dx, dz);
