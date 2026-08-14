/*
 * index.html から、claude.ai の Artifact として公開できる形を生成する。
 * スマホ（iPhone など）で URL を開いて確認するための公開用。
 *
 * Artifact は <!doctype html><head></head><body> の骨組みで包まれるので、
 * こちらの doctype / html / head / body タグは取り除く必要がある。
 * <title> はタブ名・ギャラリー名になるので残す。
 *
 * このページは元から外部依存が無いので、フォントまわりの変換は要らない。
 *
 *   node netflix-wedding/build-artifact.js  →  netflix-wedding/dist/artifact.html
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
let out = src;

const cut = (re, label) => {
  if (!re.test(out)) throw new Error('変換パターンが見つかりません: ' + label);
  out = out.replace(re, '');
};

// 1. ラッパのタグ類を除去（<style> と <script> の中身、<title> は残す）
cut(/<!DOCTYPE html>\s*/i, 'doctype');
cut(/<html[^>]*>\s*/i, '<html>');
cut(/<\/html>\s*$/i, '</html>');
cut(/<head>\s*/i, '<head>');
cut(/<\/head>\s*/i, '</head>');
cut(/<body>\s*/i, '<body>');
cut(/<\/body>\s*/i, '</body>');
cut(/<meta[^>]*>\s*/gi, '<meta>');

// 2. 外部通信が無いことを念のため確認する（Artifact の CSP は外部ホストを全て遮断する）
if (/https?:\/\//.test(out.replace(/xmlns="[^"]*"/g, ''))) {
  throw new Error('外部URLへの参照が残っています');
}

// 3. Artifact には assets/ を同梱できないため、素材は必ずプレースホルダーになる。
//    そのことが分かるように、ページ内に一行だけ注記を出す。
const NOTE = `
<div id="artifact-note">タップで最初から再生　／　写真・動画は未設定のためプレースホルダー表示です</div>
<style>
#artifact-note{
  position:fixed; left:0; right:0; bottom:0; z-index:200;
  padding:6px 10px; text-align:center;
  font-family:system-ui,sans-serif; font-size:11px; line-height:1.5;
  color:rgba(255,255,255,.55); background:rgba(0,0,0,.75);
  pointer-events:none;
}
</style>
`;
out = out.replace(/<script>/, NOTE + '<script>');

fs.mkdirSync(path.join(__dirname, 'dist'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'dist', 'artifact.html'), out);
console.log('netflix-wedding/dist/artifact.html を生成しました (' + out.length + ' bytes)');
