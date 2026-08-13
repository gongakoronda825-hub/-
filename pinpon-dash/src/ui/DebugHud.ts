import type { GameState } from '../core/GameState';
import type { Player } from '../player/Player';
import type { ResidentManager } from '../residents/ResidentManager';

/**
 * 調整用の数値表示。
 *
 * このプロトタイプの目的は「遊んで数値を決めること」（指示書 §18）なので、
 * 危険度や住民の状態が実際にどう動いているかが見えないと調整のしようがない。
 * 邪魔なときはタップで薄くなる。
 */
export class DebugHud {
  private readonly element: HTMLElement;
  private frames = 0;
  private elapsed = 0;
  private fps = 0;

  constructor(parent: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'debug';
    parent.appendChild(this.element);

    this.element.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.element.classList.toggle('dim');
    });
  }

  update(
    dt: number,
    state: GameState,
    player: Player,
    residents: ResidentManager,
    gauge: number,
    yaw: number,
  ): void {
    this.frames += 1;
    this.elapsed += dt;
    if (this.elapsed >= 0.5) {
      this.fps = Math.round(this.frames / this.elapsed);
      this.frames = 0;
      this.elapsed = 0;
    }

    const tier = state.tier;
    this.element.textContent = [
      `${this.fps}fps  x${player.position.x.toFixed(1)} z${player.position.z.toFixed(1)} ${Math.round(((-yaw * 180) / Math.PI + 360) % 360)}°`,
      `危険度 ${state.danger.toFixed(1)} [${tier.label}] ×${tier.pointMultiplier}`,
      `コンボ ${state.combo}  出現率 ${Math.round(state.spawnChance() * 100)}%  住民 ${residents.count}人`,
      `視認 ${gauge.toFixed(2)}  ${residents.describeStates()}`,
    ].join('\n');
  }
}
