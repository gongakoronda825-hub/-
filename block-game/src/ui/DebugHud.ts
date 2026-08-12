import type { Player } from '../player/Player';
import type { World } from '../world/World';

/** HUD に出す情報。呼び出し側が毎フレーム詰める。 */
export interface HudStats {
  player: Player;
  world: World;
  /** 手に持っているブロックの名前。 */
  hold: string;
  /** 読み込み済みチャンク数。 */
  chunks: number;
  /** 生きている動物の数。 */
  mobs: number;
  /** いちばん近い動物までの距離。いなければ null。 */
  nearestMob: number | null;
}

/**
 * 座標・FPS・接地状態などの簡易表示。
 * 実機で挙動を追うためのもの。タップで表示の濃さを切り替えられる。
 */
export class DebugHud {
  private readonly element: HTMLElement;
  private frames = 0;
  private elapsed = 0;

  constructor(parent: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'debug';
    this.element.textContent = '…';
    // 遊ぶ側には要らないので、既定では薄く。タップすれば読める濃さに戻る。
    this.element.classList.add('dim');
    this.element.addEventListener('pointerdown', (e) => {
      e.stopPropagation();
      this.element.classList.toggle('dim');
    });
    parent.appendChild(this.element);
  }

  update(dt: number, stats: HudStats): void {
    this.frames++;
    this.elapsed += dt;
    if (this.elapsed < 0.25) return;

    const fps = this.frames / this.elapsed;
    this.frames = 0;
    this.elapsed = 0;

    const p = stats.player.position;
    const state = stats.player.flying ? '飛行' : stats.player.onGround ? '接地' : '落下中';

    this.element.textContent =
      `${fps.toFixed(0)} fps  ` +
      `xyz ${p.x.toFixed(1)} ${p.y.toFixed(1)} ${p.z.toFixed(1)}  ` +
      `${state}  ` +
      `hold ${stats.hold}  ` +
      `chunks ${stats.chunks}  ` +
      `mobs ${stats.mobs}  ` +
      `near ${stats.nearestMob === null ? '-' : stats.nearestMob.toFixed(1)}  ` +
      `edits ${stats.world.edits}`;
  }
}
