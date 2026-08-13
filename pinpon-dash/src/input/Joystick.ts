import nipplejs from 'nipplejs';

/**
 * 画面左側のバーチャルジョイスティック（移動入力）。
 *
 * タッチの取り回しは枯れている nipplejs に任せる。視点操作は画面右半分の
 * 別要素が受け持つので、指が競合することはない。
 *
 * PC で動作確認するとき用に WASD / 矢印キーも受け付ける。
 */
export class Joystick {
  /** -1〜1。x = 右、y = 前。 */
  readonly value = { x: 0, y: 0 };

  private readonly keys = new Set<string>();
  private readonly manager: ReturnType<typeof nipplejs.create>;

  constructor(zone: HTMLElement) {
    this.manager = nipplejs.create({
      zone,
      mode: 'static',
      // ゾーンは左半分いっぱい（静的モードなのでどこを触っても効く）だが、
      // 見た目は親指の届く左下に置く。
      position: { left: '50%', bottom: '24%' },
      color: 'rgba(255,255,255,0.85)',
      size: 120,
      restJoystick: true,
      restOpacity: 0.8,
    });

    // nipplejs v1 のハンドラは { type, target, data } を1つ受け取る
    this.manager.on('move', ({ data }) => {
      if (!data?.vector) return;
      const force = Math.min(data.force ?? 1, 1);
      this.value.x = data.vector.x * force;
      this.value.y = data.vector.y * force;
    });

    this.manager.on('end', () => {
      this.value.x = 0;
      this.value.y = 0;
    });

    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
  }

  /** キーボード入力を合成した最終的な移動入力（長さ1にクランプ済み）。 */
  read(): { x: number; y: number } {
    let x = this.value.x;
    let y = this.value.y;

    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) x -= 1;
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) x += 1;
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) y -= 1;
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) y += 1;

    const length = Math.hypot(x, y);
    if (length > 1) {
      x /= length;
      y /= length;
    }
    return { x, y };
  }

  /** PC 確認用。Shift を押している間はダッシュ扱い。 */
  get shiftHeld(): boolean {
    return this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
  }

  /** PC 確認用。Space / E でピンポン。押した1フレームだけ true を返す。 */
  consumeActionKey(): boolean {
    const pressed = this.keys.has('Space') || this.keys.has('KeyE');
    if (!pressed) return false;
    this.keys.delete('Space');
    this.keys.delete('KeyE');
    return true;
  }

  private readonly onKeyDown = (e: KeyboardEvent): void => {
    this.keys.add(e.code);
  };

  private readonly onKeyUp = (e: KeyboardEvent): void => {
    this.keys.delete(e.code);
  };

  destroy(): void {
    this.manager.destroy();
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
  }
}
