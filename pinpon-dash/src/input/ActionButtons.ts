/**
 * 画面上のボタン。
 *
 * `pointerdown` で発火する（`click` だとタッチの反応が一拍遅れる。
 * ピンポンは「押した瞬間に鳴る」ことが気持ちよさの全部なので、ここは譲れない）。
 * ボタンは視点操作ゾーンの兄弟要素なので、押しても視点は動かない。
 */

/** 押した瞬間に1回だけ反応するボタン。 */
export function bindTap(button: HTMLElement, action: () => void): void {
  button.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    e.stopPropagation();
    button.classList.add('pressed');
    action();
  });
  bindRelease(button, () => button.classList.remove('pressed'));
}

/** 押している間ずっと効くボタン。 */
export function bindHold(button: HTMLElement, onDown: () => void, onUp: () => void): void {
  button.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    e.stopPropagation();
    button.classList.add('pressed');
    onDown();

    // 指が要素の外へ滑っても押しっぱなし扱いにする。
    // 対象のポインタが既に離れていると例外になるので、失敗しても無視する。
    try {
      button.setPointerCapture(e.pointerId);
    } catch {
      /* キャプチャなしで続行 */
    }
  });
  bindRelease(button, () => {
    button.classList.remove('pressed');
    onUp();
  });
}

function bindRelease(button: HTMLElement, release: () => void): void {
  for (const type of ['pointerup', 'pointercancel', 'pointerleave'] as const) {
    button.addEventListener(type, release);
  }
}

/**
 * ダッシュボタン。押している間だけ true になる。
 * 逃げながら押しっぱなしにするものなので、トグルにはしない。
 */
export class DashButton {
  held = false;

  constructor(private readonly button: HTMLElement) {
    bindHold(
      button,
      () => {
        this.held = true;
      },
      () => {
        this.held = false;
      },
    );
  }

  /** スタミナ切れを見た目に出す。 */
  setEmpty(empty: boolean): void {
    this.button.classList.toggle('empty', empty);
  }
}
