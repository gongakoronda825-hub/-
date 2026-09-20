/*
 * 画面。低解像度のドット絵を、スマホの縦画面いっぱいに引き伸ばす。
 *
 * キャンバスの内部解像度は端末に関係なく 240 ドット前後に固定している。
 * これでどの端末でも「ドットの大きさ」が同じに見え、拡大は image-rendering:pixelated
 * にブラウザ側でやらせる（縦横比は実画面と必ず一致させるので歪まない）。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});

  function create(canvas) {
    const ctx = canvas.getContext('2d', { alpha: false });
    const d = {
      canvas,
      ctx,
      w: 0,
      h: 0,
      cam: { x: 0, y: 0 },
      onresize: null,
    };

    d.resize = function () {
      const cssW = Math.max(1, global.innerWidth);
      const cssH = Math.max(1, global.innerHeight);
      const cfg = FT.config;
      const shortCss = Math.min(cssW, cssH);
      const longCss = Math.max(cssW, cssH);
      let shortPx = cfg.BASE_SHORT_SIDE;
      let longPx = Math.round((shortPx * longCss) / shortCss);
      if (longPx > cfg.BASE_LONG_SIDE_MAX) {
        longPx = cfg.BASE_LONG_SIDE_MAX;
        shortPx = Math.round((longPx * shortCss) / longCss);
      }
      const w = cssW <= cssH ? shortPx : longPx;
      const h = cssW <= cssH ? longPx : shortPx;
      if (w === d.w && h === d.h) return false;
      d.w = w; d.h = h;
      canvas.width = w;
      canvas.height = h;
      ctx.imageSmoothingEnabled = false;
      if (d.onresize) d.onresize(w, h);
      return true;
    };

    d.resize();
    global.addEventListener('resize', () => d.resize());
    global.addEventListener('orientationchange', () => setTimeout(() => d.resize(), 120));
    return d;
  }

  FT.display = { create };
})(window);
