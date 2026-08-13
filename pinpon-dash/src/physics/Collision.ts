/**
 * 当たり判定と視線判定。
 *
 * 街は平らで、遮蔽物はすべて軸に沿った箱なので、判定は XZ 平面の2次元で足りる。
 * 物理エンジンは使わない。
 *
 * 箱は2つのフラグを持つ:
 *   solid  … 通り抜けられない（移動を止める）
 *   opaque … 向こう側が見えない（視線を止める）
 *
 * 電柱のように「ぶつかるが視線は通る」ものと、生け垣のように
 * 「ぶつかって視線も切る」ものを、同じ仕組みで表現するため。
 */

export interface Box2 {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
  solid: boolean;
  opaque: boolean;
}

/** ざっくりした空間分割の1マス。総当たりを避けるためだけのもの。 */
const GRID = 10;

export class ColliderSet {
  private readonly boxes: Box2[] = [];

  /** グリッドの各マスに、そこへ重なる箱の添字を入れておく。 */
  private readonly buckets = new Map<number, number[]>();

  add(box: Box2): void {
    const index = this.boxes.length;
    this.boxes.push(box);

    const c0 = Math.floor(box.minX / GRID);
    const c1 = Math.floor(box.maxX / GRID);
    const r0 = Math.floor(box.minZ / GRID);
    const r1 = Math.floor(box.maxZ / GRID);
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        const key = this.key(c, r);
        const bucket = this.buckets.get(key);
        if (bucket) bucket.push(index);
        else this.buckets.set(key, [index]);
      }
    }
  }

  /** 箱をまとめて足す。中心とサイズで指定するほうが組み立て側は書きやすい。 */
  addBox(
    x: number,
    z: number,
    width: number,
    depth: number,
    options: { solid?: boolean; opaque?: boolean } = {},
  ): void {
    this.add({
      minX: x - width / 2,
      maxX: x + width / 2,
      minZ: z - depth / 2,
      maxZ: z + depth / 2,
      solid: options.solid ?? true,
      opaque: options.opaque ?? true,
    });
  }

  private key(col: number, row: number): number {
    // 座標は負にもなるので、適当な大きさでずらして1つの数値に潰す
    return (row + 512) * 4096 + (col + 512);
  }

  /** 位置の周りにある箱の添字。重複を除くのは呼び出し側の責任にしない。 */
  private near(minX: number, maxX: number, minZ: number, maxZ: number): number[] {
    const found: number[] = [];
    const c0 = Math.floor(minX / GRID);
    const c1 = Math.floor(maxX / GRID);
    const r0 = Math.floor(minZ / GRID);
    const r1 = Math.floor(maxZ / GRID);
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        const bucket = this.buckets.get(this.key(c, r));
        if (!bucket) continue;
        for (const index of bucket) {
          if (!found.includes(index)) found.push(index);
        }
      }
    }
    return found;
  }

  /**
   * 半径 radius の円を、めり込んだ箱から押し出す。戻り値は補正後の位置。
   *
   * 押し出しは「最も浅い1軸」だけを動かす。斜めに押し戻すと壁ぎわを
   * 歩いたときに引っかかるため。角では複数の箱に触れるので数回まわす。
   */
  resolveCircle(x: number, z: number, radius: number): { x: number; z: number } {
    let px = x;
    let pz = z;

    for (let pass = 0; pass < 3; pass++) {
      let moved = false;
      const candidates = this.near(px - radius, px + radius, pz - radius, pz + radius);

      for (const index of candidates) {
        const box = this.boxes[index];
        if (!box.solid) continue;

        // 円の中心から見て、箱の中でいちばん近い点
        const nearestX = Math.min(Math.max(px, box.minX), box.maxX);
        const nearestZ = Math.min(Math.max(pz, box.minZ), box.maxZ);
        const dx = px - nearestX;
        const dz = pz - nearestZ;
        const distanceSq = dx * dx + dz * dz;

        if (distanceSq > radius * radius) continue;

        if (distanceSq > 1e-8) {
          // 箱の外にいて、面か角にめり込んでいる
          const distance = Math.sqrt(distanceSq);
          const push = radius - distance;
          px += (dx / distance) * push;
          pz += (dz / distance) * push;
        } else {
          // 中心が箱の中に入ってしまった場合は、いちばん近い面から出す
          const left = px - box.minX;
          const right = box.maxX - px;
          const up = pz - box.minZ;
          const down = box.maxZ - pz;
          const min = Math.min(left, right, up, down);
          if (min === left) px = box.minX - radius;
          else if (min === right) px = box.maxX + radius;
          else if (min === up) pz = box.minZ - radius;
          else pz = box.maxZ + radius;
        }
        moved = true;
      }

      if (!moved) break;
    }

    return { x: px, z: pz };
  }

  /** その場所に半径 radius の円を置けるか（住民の進路チェックに使う）。 */
  free(x: number, z: number, radius: number): boolean {
    for (const index of this.near(x - radius, x + radius, z - radius, z + radius)) {
      const box = this.boxes[index];
      if (!box.solid) continue;
      const nearestX = Math.min(Math.max(x, box.minX), box.maxX);
      const nearestZ = Math.min(Math.max(z, box.minZ), box.maxZ);
      const dx = x - nearestX;
      const dz = z - nearestZ;
      if (dx * dx + dz * dz <= radius * radius) return false;
    }
    return true;
  }

  /**
   * 2点のあいだが見通せるか。opaque な箱に1つでも当たれば見えない。
   *
   * スラブ法（各軸で線分が箱の範囲に入る区間を求め、重なりがあれば交差）。
   */
  canSee(ax: number, az: number, bx: number, bz: number): boolean {
    const dx = bx - ax;
    const dz = bz - az;

    const candidates = this.near(
      Math.min(ax, bx),
      Math.max(ax, bx),
      Math.min(az, bz),
      Math.max(az, bz),
    );

    for (const index of candidates) {
      const box = this.boxes[index];
      if (!box.opaque) continue;
      if (this.segmentHitsBox(ax, az, dx, dz, box)) return false;
    }
    return true;
  }

  private segmentHitsBox(ax: number, az: number, dx: number, dz: number, box: Box2): boolean {
    let tMin = 0;
    let tMax = 1;

    // X 軸
    if (Math.abs(dx) < 1e-8) {
      if (ax < box.minX || ax > box.maxX) return false;
    } else {
      let t0 = (box.minX - ax) / dx;
      let t1 = (box.maxX - ax) / dx;
      if (t0 > t1) [t0, t1] = [t1, t0];
      tMin = Math.max(tMin, t0);
      tMax = Math.min(tMax, t1);
      if (tMin > tMax) return false;
    }

    // Z 軸
    if (Math.abs(dz) < 1e-8) {
      if (az < box.minZ || az > box.maxZ) return false;
    } else {
      let t0 = (box.minZ - az) / dz;
      let t1 = (box.maxZ - az) / dz;
      if (t0 > t1) [t0, t1] = [t1, t0];
      tMin = Math.max(tMin, t0);
      tMax = Math.min(tMax, t1);
      if (tMin > tMax) return false;
    }

    return true;
  }
}
