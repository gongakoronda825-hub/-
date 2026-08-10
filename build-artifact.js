/*
 * index.html から、claude.ai の Artifact として公開できる形を生成する。
 *
 * Artifact は <!doctype html><head></head><body> の骨組みで包まれるので、
 * こちらの doctype / html / head / body タグは取り除く必要がある。
 * また Artifact の CSP は外部ホストへの通信を全て遮断するため、
 * Web フォントの link と @font-face も外し、monospace 前提にする。
 *
 *   node build-artifact.js  →  dist/artifact.html
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
let out = src;

const cut = (re, label) => {
  if (!re.test(out)) throw new Error('変換パターンが見つかりません: ' + label);
  out = out.replace(re, '');
};

// 1. ラッパのタグ類を除去（<style> と <script> の中身は残す）
cut(/<!DOCTYPE html>\s*/i, 'doctype');
cut(/<html[^>]*>\s*/i, '<html>');
cut(/<\/html>\s*$/i, '</html>');
cut(/<head>\s*/i, '<head>');
cut(/<\/head>\s*/i, '</head>');
cut(/<body>\s*/i, '<body>');
cut(/<\/body>\s*/i, '</body>');
cut(/<meta[^>]*>\s*/gi, '<meta>');

// 2. 外部フォントは CSP で確実に落ちるので、参照ごと削除する
cut(/<link[^>]*>\s*/gi, '<link>');
cut(/\/\* PixelMplus[^*]*\*\/\s*/, 'フォント注釈');
cut(/@font-face\{[\s\S]*?\}\s*/, '@font-face');

// 3. フォント指定を monospace 系に寄せる（CSS と Canvas の両方）
const CSS_STACK = "ui-monospace,'SFMono-Regular',Menlo,'MS Gothic',monospace";
out = out
  .replace(/'PixelMplus12','DotGothic16','MS Gothic',monospace/g, CSS_STACK)
  .replace(/"PixelMplus12","DotGothic16","MS Gothic",monospace/g,
           '"SFMono-Regular",Menlo,"MS Gothic",monospace');

// 4. フォント読み込み待ちの後処理は不要になるので落とす
out = out.replace(
  /try \{\s*if \(document\.fonts && document\.fonts\.load\)\{[\s\S]*?catch \(e\)\{ \/\* フォールバックのまま続行 \*\/ \}/,
  '// Artifact では外部フォントを読まないため、フォント待ちの処理は無い'
);

// 5. プレビュー用の警告バナーは、実行環境が保証されるこちらでは不要
out = out.replace(/<div id="nojs">[\s\S]*?<\/div>\s*/, '');

if (/<link|@font-face|PixelMplus/.test(out)) {
  throw new Error('外部フォント参照が残っています');
}

fs.mkdirSync(path.join(__dirname, 'dist'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'dist', 'artifact.html'), out);
console.log('dist/artifact.html を生成しました (' + out.length + ' bytes)');
