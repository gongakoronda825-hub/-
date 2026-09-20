/*
 * ドット絵を「描く」ための最小限の道具箱。
 *
 * スプライトは Uint8Array のインデックスバッファ（0 = 透明、1以上 = パレット番号）
 * として組み立てる。最後に toCanvas() で 1ドット=1px のキャンバスに焼く。
 * アンチエイリアスが一切かからないので、拡大してもドットが濁らない。
 *
 * 影の付け方は「円柱シェーディング」。骨（折れ線）と太さを与えると、
 * 光源（左上・手前）に対する向きで明暗を選ぶ。恐竜の首も脚も同じ規則で塗れる。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});
  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

  // 光源。左上から。z成分を小さくすると、明→暗の幅が広がって立体感が出る。
  const LIGHT = [-0.48, -0.80, 0.30];

  function buf(w, h) {
    return { w: w | 0, h: h | 0, d: new Uint8Array((w | 0) * (h | 0)) };
  }

  function set(b, x, y, v) {
    x |= 0; y |= 0;
    if (x < 0 || y < 0 || x >= b.w || y >= b.h) return;
    b.d[y * b.w + x] = v;
  }

  function get(b, x, y) {
    x |= 0; y |= 0;
    if (x < 0 || y < 0 || x >= b.w || y >= b.h) return 0;
    return b.d[y * b.w + x];
  }

  function rect(b, x, y, w, h, v) {
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) set(b, x + i, y + j, v);
  }

  /** 明るさ(-1..1) → tones 配列のインデックス。境界はチェッカーでディザる。 */
  function toneAt(tones, bright, x, y, dither) {
    const n = tones.length;
    let f = clamp((bright + 0.86) / 1.72, 0, 0.9999) * n;
    let i = Math.floor(f);
    if (dither !== false) {
      const frac = f - i;
      if (frac > 0.76 && ((x + y) & 1) === 0 && i + 1 < n) i += 1;
      else if (frac < 0.24 && ((x + y) & 1) === 1 && i > 0) i -= 1;
    }
    return tones[clamp(i, 0, n - 1)];
  }

  /**
   * 骨に沿った円柱を塗る。
   * pts: [[x, y, r], ...]（最低2点）。tones: 暗→明のパレット番号配列。
   */
  function limb(b, pts, tones, opts) {
    opts = opts || {};
    const light = opts.light || LIGHT;
    const dither = opts.dither;
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], c = pts[i + 1];
      const dx = c[0] - a[0], dy = c[1] - a[1];
      const len = Math.hypot(dx, dy);
      const steps = Math.max(1, Math.ceil(len * 2));
      const nx = len > 0 ? -dy / len : 0;
      const ny = len > 0 ? dx / len : -1;
      for (let s = 0; s <= steps; s++) {
        const t = s / steps;
        const cx = a[0] + dx * t, cy = a[1] + dy * t;
        const r = a[2] + (c[2] - a[2]) * t;
        const ri = Math.ceil(r);
        for (let oy = -ri; oy <= ri; oy++) {
          for (let ox = -ri; ox <= ri; ox++) {
            if (ox * ox + oy * oy > r * r) continue;
            const px = Math.round(cx + ox), py = Math.round(cy + oy);
            // 骨に対する横方向のずれ（-1..1）から円柱の法線を作る
            const u = r > 0.001 ? clamp((ox * nx + oy * ny) / r, -1, 1) : 0;
            const bright = nx * u * light[0] + ny * u * light[1] + Math.sqrt(1 - u * u) * light[2];
            set(b, px, py, toneAt(tones, bright, px, py, dither));
          }
        }
      }
    }
  }

  /** 球。頭や実のような丸いもの用。 */
  function blob(b, x, y, r, tones, opts) {
    opts = opts || {};
    const light = opts.light || LIGHT;
    const ri = Math.ceil(r);
    for (let oy = -ri; oy <= ri; oy++) {
      for (let ox = -ri; ox <= ri; ox++) {
        const d2 = ox * ox + oy * oy;
        if (d2 > r * r) continue;
        const nx = ox / r, ny = oy / r;
        const nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
        const bright = nx * light[0] + ny * light[1] + nz * light[2];
        const px = Math.round(x + ox), py = Math.round(y + oy);
        set(b, px, py, toneAt(tones, bright, px, py, opts.dither));
      }
    }
  }

  /** 多角形の塗り。翼膜・背びれ・岩の面などに使う。 */
  function poly(b, pts, v) {
    let minY = Infinity, maxY = -Infinity;
    for (const p of pts) { minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]); }
    minY = Math.floor(minY); maxY = Math.ceil(maxY);
    const xs = [];
    for (let y = minY; y <= maxY; y++) {
      xs.length = 0;
      const sy = y + 0.5;
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], c = pts[(i + 1) % pts.length];
        if ((a[1] <= sy && c[1] > sy) || (c[1] <= sy && a[1] > sy)) {
          xs.push(a[0] + ((sy - a[1]) / (c[1] - a[1])) * (c[0] - a[0]));
        }
      }
      xs.sort((p, q) => p - q);
      for (let i = 0; i + 1 < xs.length; i += 2) {
        const x0 = Math.round(xs[i]), x1 = Math.round(xs[i + 1]);
        for (let x = x0; x <= x1; x++) {
          const val = typeof v === 'function' ? v(x, y) : v;
          if (val) set(b, x, y, val);
        }
      }
    }
  }

  /** 中身のある画素の外周1pxを輪郭色で囲む。ドット絵の輪郭線。 */
  function outline(b, v, opts) {
    opts = opts || {};
    const src = b.d.slice();
    const bottomOnly = opts.bottomOnly;
    for (let y = 0; y < b.h; y++) {
      for (let x = 0; x < b.w; x++) {
        if (src[y * b.w + x] !== 0) continue;
        let near = false;
        if (x > 0 && src[y * b.w + x - 1]) near = true;
        if (!near && x < b.w - 1 && src[y * b.w + x + 1]) near = true;
        if (!near && y > 0 && src[(y - 1) * b.w + x]) near = !bottomOnly;
        if (!near && y < b.h - 1 && src[(y + 1) * b.w + x]) near = true;
        if (near) b.d[y * b.w + x] = v;
      }
    }
  }

  /** 体の模様。暗くする方向に1段ずらす。 */
  function stripes(b, opts) {
    const period = opts.period || 7;
    const width = opts.width || 2;
    const slant = opts.slant === undefined ? 2 : opts.slant;
    const map = opts.map; // {from: to}
    for (let y = 0; y < b.h; y++) {
      for (let x = 0; x < b.w; x++) {
        const v = b.d[y * b.w + x];
        if (!v || map[v] === undefined) continue;
        const phase = (x * slant + y * 3) % period;
        if (phase < width) b.d[y * b.w + x] = map[v];
      }
    }
  }

  function hexToRgb(hex) {
    const h = hex.replace('#', '');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  /** インデックスバッファ → キャンバス。palette[0] は透明として無視される。 */
  function toCanvas(b, palette) {
    const cv = document.createElement('canvas');
    cv.width = b.w; cv.height = b.h;
    const ctx = cv.getContext('2d');
    const img = ctx.createImageData(b.w, b.h);
    const out = new Uint32Array(img.data.buffer);
    const packed = palette.map((c) => {
      if (!c) return 0;
      const [r, g, bl] = hexToRgb(c);
      return (255 << 24) | (bl << 16) | (g << 8) | r;
    });
    for (let i = 0; i < b.d.length; i++) {
      const v = b.d[i];
      if (v) out[i] = packed[v] || 0;
    }
    ctx.putImageData(img, 0, 0);
    return cv;
  }

  /** 楕円のやわらかい影。ディザで半透明にしてドット感を保つ。 */
  function shadowSprite(rx, ry, alpha) {
    const w = rx * 2 + 1, h = ry * 2 + 1;
    const cv = document.createElement('canvas');
    cv.width = w; cv.height = h;
    const ctx = cv.getContext('2d');
    const img = ctx.createImageData(w, h);
    const out = new Uint32Array(img.data.buffer);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const nx = (x - rx) / rx, ny = (y - ry) / ry;
        const d = nx * nx + ny * ny;
        if (d > 1) continue;
        let a = alpha * (1 - d * 0.45);
        if (d > 0.62 && ((x + y) & 1) === 0) a *= 0.35;
        out[y * w + x] = (Math.round(a * 255) << 24) | (26 << 16) | (18 << 8) | 8;
      }
    }
    ctx.putImageData(img, 0, 0);
    return cv;
  }

  FT.pixel = { buf, set, get, rect, limb, blob, poly, outline, stripes, toCanvas, shadowSprite, LIGHT, clamp };
})(window);
