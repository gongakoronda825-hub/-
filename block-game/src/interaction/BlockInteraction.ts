import * as THREE from 'three';
import { REACH } from '../core/config';
import type { Player } from '../player/Player';
import type { BlockType } from '../world/blocks';
import { World, type BlockPos } from '../world/World';

/** レイキャストの結果。狙っているブロックと、置くならどこか。 */
interface Target {
  /** 当たったブロック（＝「壊す」の対象）。 */
  block: BlockPos;
  /** 当たった面の隣のセル（＝「置く」の対象）。 */
  adjacent: BlockPos;
  distance: number;
}

/**
 * 画面中央からのレイキャストによる破壊・設置（計画書 §3.5）。
 *
 * 一人称なので照準は常に画面中央。`raycaster.far = REACH` にしてあり、
 * リーチ外や空を向いているときは交差が無く、何も起きない。
 */
export class BlockInteraction {
  private readonly raycaster = new THREE.Raycaster();
  private readonly center = new THREE.Vector2(0, 0);
  private readonly normalMatrix = new THREE.Matrix3();
  private readonly worldNormal = new THREE.Vector3();

  /** 狙っているブロックを縁取る枠。当たっていないときは非表示。 */
  private readonly highlight: THREE.Group;

  constructor(
    private readonly world: World,
    private readonly player: Player,
    private readonly camera: THREE.PerspectiveCamera,
    scene: THREE.Scene,
    /** インベントリで選ばれているブロック。設置のたびに読む。 */
    private readonly selectedBlock: () => BlockType,
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

  /** 完成条件④: 狙ったブロックを壊す。 */
  breakBlock(): boolean {
    const target = this.pick();
    if (!target) return false;

    const { x, y, z } = target.block;
    return this.world.removeBlock(x, y, z);
  }

  /** 完成条件⑤: 狙った面の隣に置く。 */
  placeBlock(): boolean {
    const target = this.pick();
    if (!target) return false;

    const { x, y, z } = target.adjacent;

    // (c) リーチ以内か。raycaster.far で担保されているが明示しておく
    if (target.distance > REACH) return false;
    // (a) すでにブロックがある場所には置かない
    if (this.world.isSolid(x, y, z)) return false;
    // (b) 自分の体と重なる場所には置かない（置いた瞬間に埋まるのを防ぐ）
    if (this.player.intersectsBlock(x, y, z)) return false;

    this.world.setBlock(x, y, z, this.selectedBlock());
    return true;
  }

  /** 画面中央から前方へレイを飛ばし、最初に当たったブロックを返す。 */
  private pick(): Target | null {
    this.raycaster.setFromCamera(this.center, this.camera);

    const hits = this.raycaster.intersectObjects(this.world.meshList, false);
    for (const hit of hits) {
      const block = World.blockOf(hit.object);
      if (!block || !hit.face) continue;

      // face.normal はローカル座標なのでワールドへ変換する（計画書 §8）。
      // 回転していない箱なら一致するが、将来 Mesh を回しても壊れないようにしておく。
      this.normalMatrix.getNormalMatrix(hit.object.matrixWorld);
      this.worldNormal.copy(hit.face.normal).applyMatrix3(this.normalMatrix).normalize();

      return {
        block,
        adjacent: {
          x: block.x + Math.round(this.worldNormal.x),
          y: block.y + Math.round(this.worldNormal.y),
          z: block.z + Math.round(this.worldNormal.z),
        },
        distance: hit.distance,
      };
    }

    return null;
  }
}
