/*
 * vite build の出力を、単体で開ける1枚の HTML にまとめる。
 *
 * dist/index.html は ./assets/bundle.js と ./assets/index.css を参照するので、
 * file:// で直接開いたり、1ファイルだけ配ったりすることができない。
 * ここで中身をインライン化して play/index.html を作る。
 *
 * これが公開されるファイル。GitHub Pages（main ブランチのルートを配信）に
 * 載ると /-/block-game/play/ で遊べる。dist/ は中間出力なので追跡しない。
 *
 *   npm run single   （= vite build && node build-single.js）
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const dist = join(root, 'dist');
const publishDir = join(root, 'play');

const html = readFileSync(join(dist, 'index.html'), 'utf8');
const css = readFileSync(join(dist, 'assets', 'index.css'), 'utf8');
const js = readFileSync(join(dist, 'assets', 'bundle.js'), 'utf8');

const replace = (source, pattern, replacement, label) => {
  if (!pattern.test(source)) throw new Error(`置換パターンが見つかりません: ${label}`);
  return source.replace(pattern, () => replacement);
};

let out = html;
out = replace(
  out,
  /<link rel="stylesheet"[^>]*href="[^"]*index\.css"[^>]*>/,
  `<style>\n${css}\n</style>`,
  'stylesheet',
);
out = replace(
  out,
  /<script type="module"[^>]*src="[^"]*bundle\.js"[^>]*><\/script>/,
  `<script type="module">\n${js}\n</script>`,
  'bundle',
);

// data: の favicon 以外に外部参照が残っていないことを確認する
if (/assets\/|src="[^"]|href="(?!data:)/.test(out)) {
  throw new Error('外部参照が残っています');
}

mkdirSync(publishDir, { recursive: true });
writeFileSync(join(publishDir, 'index.html'), out);
console.log(`play/index.html を生成しました (${out.length} bytes)`);
