/*
 * 投稿ページ。
 *
 * サーバーが無いので、投稿には2つの出口を用意しています。
 *   ・この端末に追加  … すぐ自分のフィードに載る。試遊と下書き用
 *   ・公開する手順     … リポジトリに置くための配置手順とカタログ用の記述を出す
 * 前者はブラウザの中で完結し、後者はコピーして貼るだけで済む形にしてあります。
 */
(function () {
  'use strict';

  var NS = window.ASOBIBA;
  var util = NS.util, data = NS.data, ui = NS.ui, store = NS.store;

  ui.header();

  /* ID の重複判定に既存のカタログが要るので、先に読み込んでおく */
  data.load().then(function () { renderLocal(); }).then(function () { ui.footer(); });

  var dropzone = document.getElementById('dropzone');
  var fileInput = document.getElementById('file');
  var stepPreview = document.getElementById('step-preview');
  var stepForm = document.getElementById('step-form');
  var stepPublish = document.getElementById('step-publish');
  var preview = document.getElementById('preview');

  var picked = null;   // { name, size, html }
  var previewUrl = null;

  /* ------------------------------------------------------- ファイル選択 */

  dropzone.addEventListener('click', function () { fileInput.click(); });
  dropzone.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
  });

  ['dragenter', 'dragover'].forEach(function (type) {
    dropzone.addEventListener(type, function (e) {
      e.preventDefault();
      dropzone.classList.add('dragging');
    });
  });
  ['dragleave', 'drop'].forEach(function (type) {
    dropzone.addEventListener(type, function () { dropzone.classList.remove('dragging'); });
  });
  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) accept(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', function () {
    if (this.files && this.files[0]) accept(this.files[0]);
  });

  function accept(file) {
    if (!/\.html?$/i.test(file.name) && file.type !== 'text/html') {
      ui.toast('HTML ファイルを選んでください');
      return;
    }
    var reader = new FileReader();
    reader.onload = function () {
      picked = { name: file.name, size: file.size, html: String(reader.result) };
      showPreview();
    };
    reader.onerror = function () { ui.toast('ファイルを読めませんでした'); };
    reader.readAsText(file);
  }

  function showPreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(new Blob([picked.html], { type: 'text/html' }));
    preview.src = previewUrl;

    document.getElementById('filerow').innerHTML =
      ui.icons.file +
      '<span><span class="name">' + util.escape(picked.name) + '</span>' +
      '<span class="dot"></span>' + formatBytes(picked.size) + '</span>' +
      '<button class="btn js-repick" type="button">別のファイルを選ぶ</button>';
    document.querySelector('.js-repick').addEventListener('click', function () {
      fileInput.value = '';
      fileInput.click();
    });

    stepPreview.hidden = false;
    stepForm.hidden = false;
    stepPublish.hidden = true;

    var title = document.getElementById('f-title');
    if (!title.value) title.value = picked.name.replace(/\.html?$/i, '').replace(/[-_]+/g, ' ');

    stepPreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function formatBytes(n) {
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(0) + ' KB';
    return (n / 1024 / 1024).toFixed(1) + ' MB';
  }

  /* --------------------------------------------------------- カテゴリ欄 */

  document.getElementById('f-categories').innerHTML = data.categories
    .filter(function (c) { return c.id !== 'all'; })
    .map(function (c) {
      return '<label><input type="checkbox" value="' + c.id + '">' + util.escape(c.label) + '</label>';
    }).join('');

  /* ------------------------------------------------------------ 収集 */

  function collect() {
    var title = document.getElementById('f-title').value.trim();
    if (!title) {
      ui.toast('タイトルを入れてください');
      document.getElementById('f-title').focus();
      return null;
    }
    if (!picked) {
      ui.toast('ファイルを選んでください');
      return null;
    }

    var categories = Array.prototype.slice
      .call(document.querySelectorAll('#f-categories input:checked'))
      .map(function (i) { return i.value; });

    var tags = document.getElementById('f-tags').value
      .split(/[,、]/).map(function (t) { return t.trim(); })
      .filter(Boolean).slice(0, 8);

    return {
      id: uniqueId(util.slug(title)),
      title: title,
      tagline: document.getElementById('f-tagline').value.trim(),
      description: document.getElementById('f-desc').value.trim(),
      categories: categories,
      tags: tags,
      orientation: document.getElementById('f-orientation').value,
      playtime: document.getElementById('f-playtime').value.trim(),
      publishedAt: new Date().toISOString().slice(0, 10)
    };
  }

  function uniqueId(base) {
    var id = base, n = 2;
    while (data.game(id)) id = base + '-' + n++;
    return id;
  }

  /* --------------------------------------------- この端末に追加して遊ぶ */

  document.getElementById('submit').addEventListener('click', function () {
    var meta = collect();
    if (!meta) return;

    meta.html = picked.html;
    store.saveLocalGame(meta).then(function (r) {
      if (r.saved) {
        window.location.href = 'game.html?id=' + encodeURIComponent(meta.id);
        return;
      }
      if (r.reason === 'too-large') {
        ui.toast('ファイルが大きすぎて端末に保存できません（' + formatBytes(r.limit) + 'まで）');
      } else {
        ui.toast('ブラウザの保存容量がいっぱいです。下の公開手順を使ってください');
      }
      showPublish(meta);
    });
  });

  /* ------------------------------------------------------ 公開する手順 */

  document.getElementById('publish').addEventListener('click', function () {
    var meta = collect();
    if (meta) showPublish(meta);
  });

  function showPublish(meta) {
    var entry = {
      id: meta.id,
      title: meta.title,
      tagline: meta.tagline,
      description: meta.description,
      creatorId: 'あなたのクリエイターID',
      categories: meta.categories,
      tags: meta.tags,
      playUrl: 'games/' + meta.id + '/index.html',
      thumbnail: 'assets/img/thumb-' + meta.id + '.png',
      orientation: meta.orientation,
      playtime: meta.playtime,
      publishedAt: meta.publishedAt,
      updatedAt: meta.publishedAt,
      controls: [{ device: 'スマホ', text: '' }, { device: 'PC', text: '' }]
    };
    var snippet = JSON.stringify(entry, null, 2);

    document.getElementById('publish-body').innerHTML =
      '<ol class="steps-list">' +
        '<li>選んだファイルを <code>games/' + util.escape(meta.id) + '/index.html</code> という名前で置く</li>' +
        '<li>16:9 のサムネイル画像を <code>assets/img/thumb-' + util.escape(meta.id) + '.png</code> に置く' +
          '（無ければ頭文字のタイルが出ます）</li>' +
        '<li><code>data/catalog.js</code> の <code>games</code> 配列に、下の記述を足す</li>' +
        '<li>コミットしてプッシュする。次の公開でフィードに載ります</li>' +
      '</ol>' +
      '<div class="codeblock-wrap" style="margin-top:16px">' +
        '<button class="btn copy js-copy" type="button">コピー</button>' +
        '<pre class="codeblock" id="snippet">' + util.escape(snippet) + '</pre>' +
      '</div>' +
      '<div class="note" style="margin-top:16px">' +
        '<p><code>creatorId</code> は <code>data/catalog.js</code> の <code>creators</code> 配列にある ID です。' +
        'はじめての人は、そこに自分の項目を1つ足してから使ってください。</p>' +
      '</div>';

    document.querySelector('.js-copy').addEventListener('click', function () {
      var text = document.getElementById('snippet').textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          ui.toast('コピーしました');
        }, function () { ui.toast('コピーできませんでした'); });
      } else {
        ui.toast('コピーできませんでした');
      }
    });

    stepPublish.hidden = false;
    stepPublish.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ------------------------------------------ この端末に置いたゲーム一覧 */

  function renderLocal() {
    store.localGames().then(function (list) {
      var section = document.getElementById('step-local');
      if (!list.length) { section.hidden = true; return; }

      section.hidden = false;
      document.getElementById('local-list').innerHTML = list.map(function (g) {
        return '<li>' +
          '<a href="game.html?id=' + encodeURIComponent(g.id) + '">' + util.escape(g.title) + '</a>' +
          '<span class="muted">' + util.escape(util.since(g.publishedAt)) + '</span>' +
          '<button class="btn js-remove" data-id="' + util.escape(g.id) + '" type="button">削除</button>' +
        '</li>';
      }).join('');

      Array.prototype.forEach.call(document.querySelectorAll('.js-remove'), function (btn) {
        btn.addEventListener('click', function () {
          store.removeLocalGame(btn.getAttribute('data-id')).then(function () {
            ui.toast('削除しました');
            renderLocal();
          });
        });
      });
    });
  }

  window.addEventListener('pagehide', function () {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  });
})();
