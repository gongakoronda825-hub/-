/*
 * play/index.html から、claude.ai の Artifact として公開できる形を生成する。
 *
 * Artifact は <!doctype html><head></head><body> の骨組みで包まれるので、
 * こちらの doctype / html / head / body タグは取り除く必要がある。
 * <title> と <style> の中身はそのまま残す（タイトルは先頭 8KB 以内にあること）。
 *
 * GitHub Pages は main ブランチを配信するので、作業ブランチのままでは
 * /-/pinpon-dash/play/ は 404 になる。マージ前に遊んでもらうための出口がこれ。
 *
 *   npm run single && node build-artifact.js   →  dist/artifact.html
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
let out = readFileSync(join(root, 'play', 'index.html'), 'utf8');

const cut = (re, label) => {
  if (!re.test(out)) throw new Error(`変換パターンが見つかりません: ${label}`);
  out = out.replace(re, '');
};

// ラッパのタグ類を除去する（<title> <style> <script> の中身は残す）
cut(/<!DOCTYPE html>\s*/i, 'doctype');
cut(/<html[^>]*>\s*/i, '<html>');
cut(/<\/html>\s*$/i, '</html>');
cut(/<head>\s*/i, '<head>');
cut(/<\/head>\s*/i, '</head>');
cut(/<body>\s*/i, '<body>');
cut(/<\/body>\s*/i, '</body>');
cut(/<meta[^>]*>\s*/gi, '<meta>');
cut(/<link[^>]*>\s*/gi, '<link>');

// 外部への参照が残っていれば、Artifact の CSP に弾かれて動かない
if (/src="(?!data:)|href="(?!data:)/.test(out)) {
  throw new Error('外部参照が残っています');
}

mkdirSync(join(root, 'dist'), { recursive: true });
writeFileSync(join(root, 'dist', 'artifact.html'), out);
console.log(`dist/artifact.html を生成しました (${out.length} bytes)`);
