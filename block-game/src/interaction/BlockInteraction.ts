import * as THREE from 'three';
import { REACH } from '../core/config';
import type { Player } from '../player/Player';
import type { World } from '../world/World';
import { AIR, type BlockId } from '../world/blocks';

/** レイキャストの結果。狙っているブロックと、置くならどこか。 */
interface Target {
  block: THREE.Vector3;
  adjacent: THREE.Vector3;
  distance: number;
}

/**
 * 画面中央からのレイキャストによる破壊・設置。
 *
 * チャンクを1メッシュに結合したので、初期版の「Mesh ごとに座標を持たせる」
 * 方式はもう使えない。**ヒット点を面の法線ぶん押し込んで floor する**方式に変えた。
 *   壊す: floor(point - n * 0.5)
 *   置く: floor(point + n * 0.5)
 * 0.5 動かすのは、ヒット点がちょうど境界にあって floor が揺れるのを避けるため。
 *
 * `raycaster.far = REACH` なので、リーチ外や空を向いているときは交差が無く、
 * 何も起きない。
 */
export class BlockInteraction {
  private readonly raycaster = new THREE.Raycaster();
  private readonly center = new THREE.Vector2(0, 0);
  private readonly normalMatrix = new THREE.Matrix3();
  private readonly worldNormal = new THREE.Vector3();
  private readonly meshes: THREE.Object3D[] = [];

  /** 狙っているブロックを縁取る枠。当たっていないときは非表示。 */
  private readonly highlight: THREE.Group;

  constructor(
    private readonly world: World,
    private readonly player: Player,
    private readonly camera: THREE.PerspectiveCamera,
    scene: THREE.Scene,
    /** インベントリで選ばれているブロック。設置のたびに読む。 */
    private readonly selectedBlock: () => BlockId,
  ) {
    this.raycaster.far = REACH;

    // ほんの少し大きい箱にして、ブロック表面とZファイティングしないようにする。
    // 黒と白を二重に描くと、草の上でも石の上でも枠が見える。
    this.highlight = new THREE.Group();
    for (const [scale, color, opacity] of [
      [1.006, 0x000000, 0.55],
      [1.002, 0xffffff, 0.9],
    ] as const) {
      const edges = new THREE.EdgesGeometry(new THREE.BoxGeometry(scale, scale, scale));
      this.highlight.add(
        new THREE.LineSegments(
          edges,
          new THREE.LineBasicMaterial({ color, transparent: true, opacity }),
        ),
      );
    }
    this.highlight.visible = false;
    scene.add(this.highlight);
  }

  /** 毎フレーム、照準の先を枠で示す。 */
  update(): void {
    const target = this.pick();
    if (!target) {
      this.highlight.visible = false;
      return;
    }
    this.highlight.visible = true;
    this.highlight.position.set(
      target.block.x + 0.5,
      target.block.y + 0.5,
      target.block.z + 0.5,
    );
  }

  /** 狙ったブロックを壊す。 */
  breakBlock(): boolean {
    const target = this.pick();
    if (!target) return false;

    const { x, y, z } = target.block;
    // 岩盤（y=0）は抜けてしまうので壊せない
    if (y <= 0) return false;
    if (this.world.getBlock(x, y, z) === AIR) return false;

    if (!this.world.setBlock(x, y, z, AIR)) return false;
    this.world.edits++;
    return true;
  }

  /** 狙った面の隣に置く。 */
  placeBlock(): boolean {
    const target = this.pick();
    if (!target) return false;

    const { x, y, z } = target.adjacent;

    // (c) リーチ以内か。raycaster.far で担保されているが明示しておく
    if (target.distance > REACH) return false;
    // (a) すでにブロックがある場所には置かない
    if (this.world.getBlock(x, y, z) !== AIR) return false;
    // (b) 自分の体と重なる場所には置かない（置いた瞬間に埋まるのを防ぐ）
    if (this.player.intersectsBlock(x, y, z)) return false;

    if (!this.world.setBlock(x, y, z, this.selectedBlock())) return false;
    this.world.edits++;
    return true;
  }

  /** 画面中央から前方へレイを飛ばし、最初に当たったブロックを返す。 */
  private pick(): Target | null {
    this.raycaster.setFromCamera(this.center, this.camera);

    const hits = this.raycaster.intersectObjects(this.world.collectMeshes(this.meshes), false);
    for (const hit of hits) {
      if (!hit.face) continue;

      // face.normal はローカル座標なのでワールドへ変換する
      this.normalMatrix.getNormalMatrix(hit.object.matrixWorld);
      this.worldNormal.copy(hit.face.normal).applyMatrix3(this.normalMatrix).normalize();

      const block = new THREE.Vector3(
        Math.floor(hit.point.x - this.worldNormal.x * 0.5),
        Math.floor(hit.point.y - this.worldNormal.y * 0.5),
        Math.floor(hit.point.z - this.worldNormal.z * 0.5),
      );
      const adjacent = new THREE.Vector3(
        Math.floor(hit.point.x + this.worldNormal.x * 0.5),
        Math.floor(hit.point.y + this.worldNormal.y * 0.5),
        Math.floor(hit.point.z + this.worldNormal.z * 0.5),
      );

      // 葉は DoubleSide なので、内側の面に当たると法線が裏返って
      // 空気を指すことがある。その場合は次の交差を見る。
      if (this.world.getBlock(block.x, block.y, block.z) === AIR) continue;

      return { block, adjacent, distance: hit.distance };
    }

    return null;
  }
}
