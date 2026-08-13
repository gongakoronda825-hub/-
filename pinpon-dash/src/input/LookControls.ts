import { LOOK_SENSITIVITY } from '../core/config';
import type { FirstPersonCamera } from '../player/FirstPersonCamera';

/**
 * 画面右側のスワイプで視点を動かす。
 *
 * Pointer Events を使い `pointerId` ごとに指を追跡するので、
 * ジョイスティック（左半分）・視点（右半分）・ボタンの同時操作が壊れない。
 * マウスも同じイベントで流れてくるので、PC ではドラッグで見回せる。
 *
 * ピンポン・ダッシュのボタンはこの要素の子ではなく兄弟にしてあるので、
 * ボタンを押したタッチはここには届かない。
 */
export class LookControls {
  /** 視点を動かしている指。1本だけ追う。 */
  private pointerId: number | null = null;
  private lastX = 0;
  private lastY = 0;

  constructor(
    private readonly zone: HTMLElement,
    private readonly camera: FirstPersonCamera,
  ) {
    zone.addEventListener('pointerdown', this.onPointerDown);
    zone.addEventListener('pointermove', this.onPointerMove);
    zone.addEventListener('pointerup', this.onPointerUp);
    zone.addEventListener('pointercancel', this.onPointerUp);
  }

  private readonly onPointerDown = (e: PointerEvent): void => {
    if (this.pointerId !== null) return; // すでに別の指が視点を持っている
    this.pointerId = e.pointerId;
    this.lastX = e.clientX;
    this.lastY = e.clientY;
    this.zone.setPointerCapture(e.pointerId);
    e.preventDefault();
  };

  private readonly onPointerMove = (e: PointerEvent): void => {
    if (e.pointerId !== this.pointerId) return;

    const dx = e.clientX - this.lastX;
    const dy = e.clientY - this.lastY;
    this.lastX = e.clientX;
    this.lastY = e.clientY;

    // 符号: 右スワイプで右を向く / 上スワイプで上を向く。
    // 好みが分かれるところなので、実機で合わないと感じたらここを反転する。
    this.camera.rotate(-dx * LOOK_SENSITIVITY, -dy * LOOK_SENSITIVITY);
    e.preventDefault();
  };

  private readonly onPointerUp = (e: PointerEvent): void => {
    if (e.pointerId !== this.pointerId) return;
    this.pointerId = null;
    if (this.zone.hasPointerCapture(e.pointerId)) {
      this.zone.releasePointerCapture(e.pointerId);
    }
  };
}
