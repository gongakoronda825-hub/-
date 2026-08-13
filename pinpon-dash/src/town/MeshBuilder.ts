import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * 街の静的な形をまとめて1つのメッシュにする道具。
 *
 * 家1軒ごとに Mesh を作ると、ドローコールが数百になってスマホで落ちる。
 * ここでは箱や円柱をいったん溜めておき、build() で1つの BufferGeometry に
 * 結合する。色はマテリアルではなく頂点カラーで持つので、
 * どれだけ色数を増やしてもマテリアルは1つのまま。
 *
 * 動かないものだけを入れること（結合後は個別に動かせない）。
 */
export class MeshBuilder {
  private readonly parts: THREE.BufferGeometry[] = [];

  /** 箱。x/z は中心、y は底面の高さ。 */
  box(
    x: number,
    y: number,
    z: number,
    width: number,
    height: number,
    depth: number,
    color: number,
    rotationY = 0,
  ): void {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    geometry.translate(0, height / 2, 0);
    if (rotationY !== 0) geometry.rotateY(rotationY);
    geometry.translate(x, y, z);
    this.push(geometry, color);
  }

  /** 円柱。電柱や木の幹に使う。 */
  cylinder(
    x: number,
    y: number,
    z: number,
    radius: number,
    height: number,
    color: number,
    segments = 6,
  ): void {
    const geometry = new THREE.CylinderGeometry(radius, radius, height, segments);
    geometry.translate(x, y + height / 2, z);
    this.push(geometry, color);
  }

  /** 横倒しの筒。空き地の土管に使う。両端は開けたまま。 */
  tube(
    x: number,
    y: number,
    z: number,
    radius: number,
    length: number,
    color: number,
    rotationY = 0,
  ): void {
    const geometry = new THREE.CylinderGeometry(radius, radius, length, 10, 1, true);
    geometry.rotateX(Math.PI / 2);
    geometry.rotateY(rotationY);
    geometry.translate(x, y + radius, z);
    this.push(geometry, color);
  }

  /**
   * 切妻屋根（三角柱）。棟は width の方向に走る。
   *
   * 3角形の円柱を横に倒して作る。素の CylinderGeometry は
   *   ・軸が Y、断面は XZ 平面
   *   ・断面の頂点は (0, 1) と (±0.866, -0.5)  ＝ 外接円の半径が 1
   * なので、寸法を指定どおりにするには 底辺 1.732 / 高さ 1.5 で割ってから
   * 拡大する。回転の順番を変えると棟の向きが変わるので注意。
   *
   * @param y 軒（屋根の底面）の高さ
   * @param width  棟の走る方向の長さ
   * @param height 軒から棟までの高さ
   * @param depth  屋根が流れる方向の幅
   */
  roof(
    x: number,
    y: number,
    z: number,
    width: number,
    height: number,
    depth: number,
    color: number,
    rotationY = 0,
  ): void {
    const geometry = new THREE.CylinderGeometry(1, 1, 1, 3);
    geometry.rotateX(-Math.PI / 2); // 押し出し方向を Z へ（頂点が上を向く）
    geometry.rotateY(Math.PI / 2); // 押し出し方向を X へ ＝ 棟が width の方向に走る
    geometry.scale(width, height / 1.5, depth / 1.732);
    geometry.translate(0, height / 3, 0); // 軒を原点の高さに合わせる
    if (rotationY !== 0) geometry.rotateY(rotationY);
    geometry.translate(x, y, z);
    this.push(geometry, color);
  }

  /** 地面など、上を向いた平らな面。 */
  plane(x: number, y: number, z: number, width: number, depth: number, color: number): void {
    const geometry = new THREE.PlaneGeometry(width, depth);
    geometry.rotateX(-Math.PI / 2);
    geometry.translate(x, y, z);
    this.push(geometry, color);
  }

  private push(geometry: THREE.BufferGeometry, color: number): void {
    const rgb = new THREE.Color(color);
    const count = geometry.getAttribute('position').count;
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      colors[i * 3] = rgb.r;
      colors[i * 3 + 1] = rgb.g;
      colors[i * 3 + 2] = rgb.b;
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // 結合には属性の顔ぶれが揃っている必要がある。UV は使わないので落とす。
    geometry.deleteAttribute('uv');
    this.parts.push(geometry);
  }

  /** 溜めた形を1つのメッシュにする。以後この MeshBuilder は使えない。 */
  build(): THREE.Mesh {
    if (this.parts.length === 0) throw new Error('形が1つも積まれていません');

    const merged = mergeGeometries(this.parts, false);
    if (!merged) throw new Error('ジオメトリの結合に失敗しました');

    for (const part of this.parts) part.dispose();
    this.parts.length = 0;

    const material = new THREE.MeshLambertMaterial({ vertexColors: true });
    const mesh = new THREE.Mesh(merged, material);
    mesh.matrixAutoUpdate = false;
    return mesh;
  }
}
