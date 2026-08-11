/**
 * 画面中央の「＋」照準。レイキャストはここから飛ぶ。
 * クリック/タッチを吸わないよう pointer-events は CSS 側で無効にしてある。
 */
export function createCrosshair(parent: HTMLElement): HTMLElement {
  const crosshair = document.createElement('div');
  crosshair.id = 'crosshair';
  crosshair.innerHTML = '<span class="bar h"></span><span class="bar v"></span>';
  parent.appendChild(crosshair);
  return crosshair;
}
