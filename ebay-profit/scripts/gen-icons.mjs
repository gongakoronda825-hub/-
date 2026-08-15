// PWAアイコンを生成する（依存なし・Nodeのzlibで最小PNGを書き出す）。
// 再生成: node scripts/gen-icons.mjs
import { deflateSync } from 'node:zlib';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const outDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'icons');
mkdirSync(outDir, { recursive: true });

const BG = [15, 23, 42]; // slate-900
const FG = [34, 197, 94]; // green-500
const FG2 = [148, 163, 184]; // slate-400

function crc32(buf) {
  let c;
  const table = [];
  for (let n = 0; n < 256; n++) {
    c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  let crc = 0xffffffff;
  for (const b of buf) crc = table[(crc ^ b) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const typeBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])));
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

function png(size, pixel) {
  const raw = Buffer.alloc(size * (size * 3 + 1));
  let o = 0;
  for (let y = 0; y < size; y++) {
    raw[o++] = 0; // filter: none
    for (let x = 0; x < size; x++) {
      const [r, g, b] = pixel(x, y, size);
      raw[o++] = r;
      raw[o++] = g;
      raw[o++] = b;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 2; // color type: truecolor
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// 右肩上がりの折れ線＋その下のバー（＝利益の伸び）のシンプルな図案
function mark(x, y, size) {
  const u = size / 32;
  const cx = x / u;
  const cy = y / u;

  // 下部のバー3本（高さが右に向かって伸びる）
  const bars = [
    { x0: 6, x1: 10, top: 22 },
    { x0: 13, x1: 17, top: 18 },
    { x0: 20, x1: 24, top: 13 },
  ];
  for (const b of bars) {
    if (cx >= b.x0 && cx <= b.x1 && cy >= b.top && cy <= 26) {
      return b.top === 13 ? FG : FG2;
    }
  }

  // 上向きの三角（右上・成長を示す）
  const ax = Math.abs(cx - 22);
  if (cy >= 4 && cy <= 10 && ax <= (cy - 4) * 0.85) return FG;

  return BG;
}

for (const size of [180, 192, 512]) {
  const buf = png(size, (x, y) => mark(x, y, size));
  writeFileSync(join(outDir, `icon-${size}.png`), buf);
  console.log(`wrote icons/icon-${size}.png (${buf.length} bytes)`);
}

// マスカブル用（余白多め＝セーフゾーン確保）
const maskable = png(512, (x, y) => {
  const inset = 512 * 0.15;
  const s = 512 - inset * 2;
  if (x < inset || y < inset || x >= 512 - inset || y >= 512 - inset) return BG;
  return mark(x - inset, y - inset, s);
});
writeFileSync(join(outDir, 'icon-maskable-512.png'), maskable);
console.log(`wrote icons/icon-maskable-512.png (${maskable.length} bytes)`);
