/*
 * ホーム（フィード）。
 * 検索語・カテゴリ・並び順は全部クエリ文字列に持たせています。URLをそのまま
 * 送れば同じ画面が開くし、ブラウザの戻るも普通に効きます。
 */
(function () {
  'use strict';

  var NS = window.ASOBIBA;
  var util = NS.util, data = NS.data, ui = NS.ui, store = NS.store;

  var params = new URLSearchParams(window.location.search);
  var q = params.get('q') || '';
  var tag = params.get('tag') || '';
  var category = params.get('category') || 'all';
  var sort = params.get('sort') || 'recommended';

  var SORTS = [
    { id: 'recommended', label: 'おすすめ順' },
    { id: 'new', label: '新着順' },
    { id: 'popular', label: 'よく遊んだ順' }
  ];

  ui.header({ q: q });

  var chipbar = document.getElementById('chipbar');
  var main = document.getElementById('main');

  function url(changes) {
    var p = new URLSearchParams(window.location.search);
    Object.keys(changes).forEach(function (k) {
      if (changes[k] === null || changes[k] === '' || changes[k] === 'all') p.delete(k);
      else p.set(k, changes[k]);
    });
    var s = p.toString();
    return 'index.html' + (s ? '?' + s : '');
  }

  function renderChipbar() {
    var html = data.categories.map(function (c) {
      return '<a class="chip" href="' + url({ category: c.id }) + '"' +
        ' aria-pressed="' + (c.id === category) + '">' + util.escape(c.label) + '</a>';
    }).join('');

    html += '<span class="spacer"></span>';
    html += '<select class="sort" id="sort" aria-label="並び順">' +
      SORTS.map(function (s) {
        return '<option value="' + s.id + '"' + (s.id === sort ? ' selected' : '') + '>' +
          util.escape(s.label) + '</option>';
      }).join('') + '</select>';

    chipbar.innerHTML = html;
    chipbar.querySelector('#sort').addEventListener('change', function () {
      window.location.href = url({ sort: this.value === 'recommended' ? null : this.value });
    });
  }

  function hero() {
    var site = NS.site || {};
    return '<section class="hero">' +
      '<h1>' + util.escape(site.tagline || '') + '</h1>' +
      '<p>審査も、開発者登録も要りません。HTMLが1枚あれば公開できて、' +
        '遊ぶ人はリンクを開くだけ。反応はプレイ数といいねで返ってきます。</p>' +
      '<div class="actions">' +
        '<a class="btn btn-primary btn-lg" href="upload.html">' + ui.icons.upload + 'ゲームを投稿する</a>' +
      '</div>' +
    '</section>';
  }

  function sectionHead(title, note) {
    return '<div class="section-head"><h2 class="section-title">' + util.escape(title) + '</h2>' +
      (note ? '<p>' + note + '</p>' : '') + '</div>';
  }

  data.load().then(function (games) {
    var ids = games.map(function (g) { return g.id; });
    return Promise.all([store.statsFor(ids), store.history(8)]);
  }).then(function (res) {
    var stats = res[0], history = res[1];

    renderChipbar();

    var results = data.query({ q: q, tag: tag, category: category, sort: sort, stats: stats });
    var filtering = !!(q || tag || category !== 'all');
    var html = '';

    if (filtering) {
      var label = q ? '「' + util.escape(q) + '」の検索結果'
        : tag ? '#' + util.escape(tag)
        : util.escape(data.categoryLabel(category));
      html += sectionHead(label, results.length + ' 件');
      html += ui.grid(results, stats, {
        emptyTitle: '見つかりませんでした',
        emptyBody: '別の言葉で探すか、カテゴリを「すべて」に戻してみてください。'
      });
    } else {
      html += hero();

      var recent = history
        .map(function (h) { return data.game(h.id); })
        .filter(Boolean)
        .slice(0, 4);

      if (recent.length) {
        html += sectionHead('最近遊んだゲーム');
        html += ui.grid(recent, stats, {});
      }

      html += sectionHead(
        SORTS.filter(function (s) { return s.id === sort; })[0].label.replace('順', ''),
        results.length + ' 件のゲーム'
      );
      html += ui.grid(results, stats, {
        emptyTitle: 'まだゲームがありません',
        emptyBody: '最初の1本を投稿してみてください。'
      });
    }

    main.innerHTML = html;
    ui.footer();
  });
})();
