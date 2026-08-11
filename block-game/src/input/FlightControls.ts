import { DOUBLE_TAP_MS } from '../core/config';
import type { Player } from '../player/Player';
import { bindHold, bindTap } from './ActionButtons';

/**
 * ジャンプと飛行。
 *
 * - 1回タップ … ジャンプ（接地しているときだけ）
 * - 2回連打  … 飛行の切り替え。飛行中は▲▼が現れる
 *
 * 連打の1回目はジャンプとしても働く。跳んだ直後にもう一度押すと飛び始める、
 * という手触りで、マイクラのクリエイティブと同じ挙動。
 */
export class FlightControls {
  private lastTapAt = 0;
  private up = false;
  private down = false;

  constructor(
    private readonly player: Player,
    private readonly buttons: {
      jump: HTMLElement;
      up: HTMLElement;
      down: HTMLElement;
    },
  ) {
    bindTap(buttons.jump, () => this.onJumpTap());

    bindHold(buttons.up, () => this.setUp(true), () => this.setUp(false));
    bindHold(buttons.down, () => this.setDown(true), () => this.setDown(false));

    // キーボードでも試せるようにしておく（PC での確認用）
    window.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      if (e.code === 'Space') this.onJumpTap();
      if (e.code === 'ShiftLeft') this.setDown(true);
    });
    window.addEventListener('keyup', (e) => {
      if (e.code === 'ShiftLeft') this.setDown(false);
    });

    this.syncButtons();
  }

  private onJumpTap(): void {
    const now = performance.now();

    if (now - this.lastTapAt < DOUBLE_TAP_MS) {
      // 連打 → 飛行の切り替え。3連打で戻らないよう履歴は捨てる
      this.lastTapAt = 0;
      this.player.setFlying(!this.player.flying);
      this.up = false;
      this.down = false;
      this.syncButtons();
      return;
    }

    this.lastTapAt = now;
    this.player.jump();
  }

  private setUp(pressed: boolean): void {
    this.up = pressed;
    this.applyVertical();
  }

  private setDown(pressed: boolean): void {
    this.down = pressed;
    this.applyVertical();
  }

  /** ▲▼を同時に押したら打ち消し合ってその高さに留まる。 */
  private applyVertical(): void {
    this.player.verticalInput = (this.up ? 1 : 0) + (this.down ? -1 : 0);
  }

  /** 飛行中だけ▲▼を出し、ジャンプボタンの見た目を切り替える。 */
  private syncButtons(): void {
    const { flying } = this.player;
    this.buttons.up.classList.toggle('hidden', !flying);
    this.buttons.down.classList.toggle('hidden', !flying);
    this.buttons.jump.classList.toggle('active', flying);
    this.buttons.jump.textContent = flying ? 'とぶ\nON' : 'ジャンプ';
    this.player.verticalInput = 0;
  }
}
