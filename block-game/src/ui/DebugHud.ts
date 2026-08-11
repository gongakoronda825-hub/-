import type { Player } from '../player/Player';
import type { World } from '../world/World';

/**
 * 座標・FPS・接地状態の簡易表示（計画書 §6）。
 * 実機で挙動を追うためのもの。タップで表示を切り替えられる。
 */
export class DebugHud {
  private readonly element: HTMLElement;
  private frames = 0;
  private elapsed = 0;
  private fps = 0;

  constructor(parent: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'debug';
    this.element.textContent = '…';
    this.element.addEventListener('pointerdown', (e) => {
      e.stopPropagation();
      this.element.classList.toggle('dim');
    });
    parent.appendChild(this.element);
  }

  update(dt: number, player: Player, world: World): void {
    this.frames++;
    this.elapsed += dt;
    if (this.elapsed < 0.25) return;

    this.fps = this.frames / this.elapsed;
    this.frames = 0;
    this.elapsed = 0;

    const p = player.position;
    this.element.textContent =
      `${this.fps.toFixed(0)} fps  ` +
      `xyz ${p.x.toFixed(1)} ${p.y.toFixed(1)} ${p.z.toFixed(1)}  ` +
      `${player.onGround ? '接地' : '落下中'}  ` +
      `blocks ${world.blockCount}`;
  }
}
