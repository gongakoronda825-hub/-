/**
 * 「壊す」「置く」ボタン。
 *
 * `pointerdown` で発火する（`click` だとタッチの反応が一拍遅れる）。
 * ボタンは視点操作ゾーンの兄弟要素なので、押しても視点は動かない。
 * ボタンを押しながら移動・視点操作を続けられる。
 */
export class ActionButtons {
  constructor(
    breakButton: HTMLElement,
    placeButton: HTMLElement,
    handlers: { onBreak: () => void; onPlace: () => void },
  ) {
    this.bind(breakButton, handlers.onBreak);
    this.bind(placeButton, handlers.onPlace);
  }

  private bind(button: HTMLElement, action: () => void): void {
    button.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      e.stopPropagation();
      button.classList.add('pressed');
      action();
    });

    const release = () => button.classList.remove('pressed');
    button.addEventListener('pointerup', release);
    button.addEventListener('pointercancel', release);
    button.addEventListener('pointerleave', release);
  }
}
