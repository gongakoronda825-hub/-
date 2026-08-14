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

// 3. assets/ のファイルをデータURIとして本文に埋め込む。
//    Artifact は1ファイルしか公開できないため、これをやらないと素材が出ない。
//    ファイルが無いスロットはそのまま残し、プレースホルダー表示に任せる。
const MIME = {
  '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png',
  '.gif':'image/gif',  '.webp':'image/webp',
  '.mp4':'video/mp4',  '.webm':'video/webm', '.mov':'video/quicktime',
};
// 同じ写真が複数のスロットで使い回されるので、データURIは1枚につき1回だけ持ち、
// 各スロットからはそれを参照する。そうしないとファイルが数倍に膨らむ。
const dataUris = new Map();   // ファイル名 → データURI
const missing  = new Set();
out = out.replace(/(['"])assets\/([^'"]+)\1/g, (whole, quote, file) => {
  const abs = path.join(__dirname, 'assets', file);
  const mime = MIME[path.extname(file).toLowerCase()];
  if (!mime || !fs.existsSync(abs)) { missing.add(file); return whole; }
  if (!dataUris.has(file)) {
    dataUris.set(file, 'data:' + mime + ';base64,' + fs.readFileSync(abs).toString('base64'));
  }
  return '__ASSETS[' + JSON.stringify(file) + ']';
});
const assetScript = dataUris.size
  ? '<script>\n/* assets/ の中身をデータURIとして埋め込んだもの（1枚につき1回だけ） */\n'
    + 'const __ASSETS = {\n'
    + [...dataUris].map(([k, v]) => JSON.stringify(k) + ':' + JSON.stringify(v)).join(',\n')
    + '\n};\n</script>\n'
  : '';
console.log('埋め込み: ' + dataUris.size + ' 件' +
            (missing.size ? ' / 未設置: ' + [...missing].join(', ') : ''));

// 4. 画面下に一行だけ注記を出す（タップで再生し直せること、未設置の素材があること）
const noteText = 'タップで最初から再生'
  + (missing.size ? '　／　' + [...missing].join('・') + ' は未設置のためプレースホルダー表示です' : '');
const NOTE = `
<div id="artifact-note">${noteText}</div>
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
// 素材の定義はメインのスクリプトより前に置く必要がある
out = out.replace(/<script>/, NOTE + assetScript + '<script>');

fs.mkdirSync(path.join(__dirname, 'dist'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'dist', 'artifact.html'), out);
console.log('netflix-wedding/dist/artifact.html を生成しました (' + out.length + ' bytes)');
