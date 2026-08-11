/**
 * 画面上のボタン共通の扱い。
 *
 * `pointerdown` で発火する（`click` だとタッチの反応が一拍遅れる）。
 * ボタンは視点操作ゾーンの兄弟要素なので、押しても視点は動かない。
 * `stopPropagation` はしているが、他の指の操作は別の要素なので止まらない
 * ＝ボタンを押しながら移動・視点操作を続けられる。
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

/** 「こわす」「おく」。 */
export class ActionButtons {
  constructor(
    breakButton: HTMLElement,
    placeButton: HTMLElement,
    handlers: { onBreak: () => void; onPlace: () => void },
  ) {
    bindTap(breakButton, handlers.onBreak);
    bindTap(placeButton, handlers.onPlace);
  }
}
