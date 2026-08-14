/*
 * 画面をまたいで使う道具一式。
 *   ASOBIBA.util … 文字列と数字の整形
 *   ASOBIBA.data … カタログの検索・並び替え・おすすめ
 *   ASOBIBA.ui   … ヘッダー、カード、トースト、テーマ
 *
 * このファイルは <head> で同期読み込みしています。テーマの適用が描画より
 * 先に走らないと、切り替えている人の画面が一瞬白く光るためです。
 */
(function () {
  'use strict';

  var NS = (window.ASOBIBA = window.ASOBIBA || {});
  var catalog = NS.catalog || { games: [], creators: [], categories: [] };

  /* ================================================================ util */

  var util = {
    escape: function (s) {
      return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    },

    /** 12345 → 1.2万。日本語で読みやすい桁に丸める */
    count: function (n) {
      n = Number(n) || 0;
      if (n < 10000) return n.toLocaleString('ja-JP');
      if (n < 100000000) {
        var man = n / 10000;
        return (man < 10 ? man.toFixed(1).replace(/\.0$/, '') : Math.floor(man)) + '万';
      }
      return (n / 100000000).toFixed(1).replace(/\.0$/, '') + '億';
    },

    /** 「3日前」。1年を超えたら日付そのもの */
    since: function (value) {
      var t = value instanceof Date ? value.getTime() : Date.parse(value);
      if (isNaN(t)) return '';
      var sec = Math.max(0, (Date.now() - t) / 1000);
      if (sec < 60) return 'たった今';
      if (sec < 3600) return Math.floor(sec / 60) + '分前';
      if (sec < 86400) return Math.floor(sec / 3600) + '時間前';
      if (sec < 86400 * 30) return Math.floor(sec / 86400) + '日前';
      if (sec < 86400 * 365) return Math.floor(sec / (86400 * 30)) + 'か月前';
      return util.date(value);
    },

    date: function (value) {
      var t = value instanceof Date ? value.getTime() : Date.parse(value);
      if (isNaN(t)) return '';
      var d = new Date(t);
      return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日';
    },

    param: function (name) {
      return new URLSearchParams(window.location.search).get(name);
    },

    /** タイトルからURLに使えるIDを作る。日本語しか無ければ game-xxxx に落とす */
    slug: function (s) {
      var base = String(s || '').toLowerCase()
        .replace(/[^a-z0-9぀-ヿ一-龯]+/g, '-')
        .replace(/^-+|-+$/g, '');
      if (!/^[a-z0-9][a-z0-9-]*$/.test(base)) {
        return 'game-' + Math.random().toString(36).slice(2, 8);
      }
      return base.slice(0, 48);
    }
  };

  /* ================================================================ data */

  /* 投稿ページからこの端末に置かれたゲームの、仮のクリエイター */
  var LOCAL_CREATOR = {
    id: '__local__',
    name: 'あなた',
    bio: 'この端末に置いたゲームです。ほかの人には見えません。',
    local: true,
    links: []
  };

  var localGamesCache = null;

  var data = {
    categories: catalog.categories || [],

    /** カタログ + この端末の投稿。読み込みは1度だけ */
    load: function () {
      if (localGamesCache) return Promise.resolve(all());
      return NS.store.localGames().then(function (list) {
        localGamesCache = list.map(function (g) {
          return {
            id: g.id,
            title: g.title,
            tagline: g.tagline || '',
            description: g.description || '',
            creatorId: LOCAL_CREATOR.id,
            categories: g.categories || [],
            tags: g.tags || [],
            playUrl: null,
            localHtml: g.html,
            thumbnail: g.thumbnail || null,
            orientation: g.orientation || 'any',
            playtime: g.playtime || '',
            publishedAt: g.publishedAt,
            updatedAt: g.publishedAt,
            controls: g.controls || [],
            isLocal: true
          };
        });
        return all();
      });
    },

    game: function (id) {
      return all().filter(function (g) { return g.id === id; })[0] || null;
    },

    creator: function (id) {
      if (id === LOCAL_CREATOR.id) return LOCAL_CREATOR;
      return (catalog.creators || []).filter(function (c) { return c.id === id; })[0] || null;
    },

    gamesByCreator: function (id) {
      return all().filter(function (g) { return g.creatorId === id; });
    },

    categoryLabel: function (id) {
      var c = (catalog.categories || []).filter(function (x) { return x.id === id; })[0];
      return c ? c.label : id;
    },

    /** 検索・カテゴリ・並び替えをまとめて適用する */
    query: function (opts) {
      opts = opts || {};
      var list = all().slice();

      if (opts.category && opts.category !== 'all') {
        list = list.filter(function (g) {
          return (g.categories || []).indexOf(opts.category) !== -1;
        });
      }

      if (opts.tag) {
        list = list.filter(function (g) {
          return (g.tags || []).indexOf(opts.tag) !== -1;
        });
      }

      var q = (opts.q || '').trim().toLowerCase();
      if (q) {
        var terms = q.split(/\s+/);
        list = list.filter(function (g) {
          var creator = data.creator(g.creatorId);
          var hay = [
            g.title, g.tagline, g.description,
            (g.tags || []).join(' '),
            (g.categories || []).map(data.categoryLabel).join(' '),
            creator ? creator.name : ''
          ].join(' ').toLowerCase();
          return terms.every(function (t) { return hay.indexOf(t) !== -1; });
        });
      }

      var stats = opts.stats || {};
      var byNew = function (a, b) {
        return Date.parse(b.publishedAt || 0) - Date.parse(a.publishedAt || 0);
      };

      if (opts.sort === 'new') {
        list.sort(byNew);
      } else if (opts.sort === 'popular') {
        list.sort(function (a, b) {
          var d = ((stats[b.id] || {}).plays || 0) - ((stats[a.id] || {}).plays || 0);
          return d !== 0 ? d : byNew(a, b);
        });
      } else {
        /* おすすめ: この端末での反応を少しだけ効かせつつ、基本は新しい順 */
        list.sort(function (a, b) {
          var sa = (stats[a.id] || {}), sb = (stats[b.id] || {});
          var score = function (s) { return (s.plays || 0) + (s.liked ? 3 : 0); };
          var d = score(sb) - score(sa);
          return d !== 0 ? d : byNew(a, b);
        });
      }

      return list;
    },

    /** 詳細ページの「次に遊ぶ」。カテゴリとタグの重なりで近いものから */
    related: function (gameId, limit) {
      var base = data.game(gameId);
      if (!base) return [];
      var overlap = function (a, b) {
        return (a || []).filter(function (x) { return (b || []).indexOf(x) !== -1; }).length;
      };
      return all()
        .filter(function (g) { return g.id !== gameId; })
        .map(function (g) {
          var score =
            overlap(g.categories, base.categories) * 3 +
            overlap(g.tags, base.tags) * 2 +
            (g.creatorId === base.creatorId ? 2 : 0);
          return { game: g, score: score };
        })
        .sort(function (a, b) {
          if (b.score !== a.score) return b.score - a.score;
          return Date.parse(b.game.publishedAt || 0) - Date.parse(a.game.publishedAt || 0);
        })
        .slice(0, limit || 8)
        .map(function (x) { return x.game; });
    },

    localCreatorId: LOCAL_CREATOR.id
  };

  function all() {
    return (catalog.games || []).concat(localGamesCache || []);
  }

  /* ============================================================== icons */

  var icons = {
    logo: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.53.85l10.2-6.5a1 1 0 0 0 0-1.7L9.53 4.65A1 1 0 0 0 8 5.5Z"/><path d="M3 7.5a1.5 1.5 0 0 1 3 0v9a1.5 1.5 0 0 1-3 0Z" opacity=".55"/></svg>',
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.53.85l10.2-6.5a1 1 0 0 0 0-1.7L9.53 4.65A1 1 0 0 0 8 5.5Z"/></svg>',
    heart: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.3 4.6 13a4.7 4.7 0 0 1 6.6-6.7l.8.8.8-.8A4.7 4.7 0 0 1 19.4 13Z"/></svg>',
    heartFull: '<svg class="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 20.3 4.6 13a4.7 4.7 0 0 1 6.6-6.7l.8.8.8-.8A4.7 4.7 0 0 1 19.4 13Z"/></svg>',
    share: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M12 15V4m0 0L8 8m4-4 4 4"/></svg>',
    upload: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v8m-4-4h8"/></svg>',
    back: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5 8 12l7 7"/></svg>',
    expand: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5"/></svg>',
    sun: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5M19.1 4.9l-1.5 1.5M6.4 17.6l-1.5 1.5"/></svg>',
    moon: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/></svg>',
    rotate: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="9.5" width="20" height="12" rx="2.5"/><path d="M8.4 6.2a7.4 7.4 0 0 1 7.2 0"/><path d="M13.4 3.4 16.4 6.1l-2.8 2.2"/></svg>',
    file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V7Z"/><path d="M14 3v4h4"/><path d="M9 13h6m-6 3.5h4"/></svg>'
  };

  /* ================================================================== ui */

  var THEME_KEY = 'asobiba.theme';

  function currentTheme() {
    try { return window.localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }

  function applyTheme(theme) {
    if (theme === 'light' || theme === 'dark') {
      document.documentElement.setAttribute('data-theme', theme);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }

  function prefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  var ui = {
    icons: icons,

    /** ヘッダーを差し込む。active は 'home' | 'upload' など */
    header: function (opts) {
      opts = opts || {};
      var site = NS.site || { name: 'あそびば' };
      var q = util.escape(opts.q || '');
      var dark = currentTheme() ? currentTheme() === 'dark' : prefersDark();

      var el = document.createElement('header');
      el.className = 'site-header';
      el.innerHTML =
        '<a class="logo" href="index.html">' +
          '<span class="logo-mark">' + icons.logo + '</span>' +
          '<span class="logo-text">' + util.escape(site.name) + '</span>' +
        '</a>' +
        '<form class="search" role="search" action="index.html">' +
          '<label class="visually-hidden" for="q">ゲームをさがす</label>' +
          '<input id="q" name="q" type="search" placeholder="ゲームをさがす" value="' + q + '" autocomplete="off">' +
          '<button type="submit" aria-label="さがす">' + icons.search + '</button>' +
        '</form>' +
        '<div class="header-actions">' +
          '<button class="btn btn-icon js-theme" type="button" aria-label="配色を切り替える" title="配色を切り替える">' +
            (dark ? icons.sun : icons.moon) +
          '</button>' +
          '<a class="btn btn-primary" href="upload.html">' + icons.upload + '<span>投稿する</span></a>' +
        '</div>';

      document.body.insertBefore(el, document.body.firstChild);

      el.querySelector('.js-theme').addEventListener('click', function () {
        var next = (currentTheme() ? currentTheme() === 'dark' : prefersDark()) ? 'light' : 'dark';
        try { window.localStorage.setItem(THEME_KEY, next); } catch (e) { /* 保存できなくても切り替えは効く */ }
        applyTheme(next);
        this.innerHTML = next === 'dark' ? icons.sun : icons.moon;
      });

      return el;
    },

    footer: function () {
      var site = NS.site || {};
      var el = document.createElement('footer');
      el.className = 'site-footer';
      el.innerHTML =
        '<p>プレイ数・いいね・フォローは、いまのところ<strong>この端末の中だけ</strong>に記録されます。' +
        '別の端末や他の人には共有されません。</p>' +
        (site.repoUrl
          ? '<p><a href="' + util.escape(site.repoUrl) + '">ソースコード</a> · ' +
            '<a href="upload.html">ゲームを投稿する</a></p>'
          : '');
      document.body.appendChild(el);
      return el;
    },

    /** サムネイル部分。画像が無ければ頭文字のグラデーションで埋める */
    thumb: function (game, stats) {
      var badges = '';
      if (game.isLocal) badges += '<span class="badge badge-left">あなたの投稿</span>';
      if (game.playtime) badges += '<span class="badge">' + util.escape(game.playtime) + '</span>';
      else if (game.orientation === 'landscape') badges += '<span class="badge">横画面</span>';

      var inner = game.thumbnail
        ? '<img src="' + util.escape(game.thumbnail) + '" alt="" loading="lazy" decoding="async">'
        : '<div class="thumb-fallback">' + util.escape(String(game.title || '?').slice(0, 1)) + '</div>';

      return '<div class="thumb">' + inner +
        '<div class="play-veil"><span>' + icons.play + '</span></div>' +
        badges + '</div>';
    },

    /** フィードのカード1枚 */
    card: function (game, stats) {
      stats = stats || {};
      var creator = data.creator(game.creatorId) || { name: '' };
      var initial = util.escape(String(creator.name || '?').slice(0, 1));
      var meta = 'プレイ ' + util.count(stats.plays || 0) + '回' +
        '<span class="dot"></span>' + util.escape(util.since(game.publishedAt));

      return '<a class="card" href="game.html?id=' + encodeURIComponent(game.id) + '">' +
        ui.thumb(game, stats) +
        '<div class="card-body">' +
          '<span class="avatar avatar-sm" aria-hidden="true">' + initial + '</span>' +
          '<div>' +
            '<h3 class="card-title">' + util.escape(game.title) + '</h3>' +
            '<p class="card-meta">' + util.escape(creator.name) + '</p>' +
            '<p class="card-meta">' + meta + '</p>' +
          '</div>' +
        '</div>' +
      '</a>';
    },

    /** サイドバー用の横並びカード */
    sideCard: function (game, stats) {
      stats = stats || {};
      var creator = data.creator(game.creatorId) || { name: '' };
      return '<a class="side-card" href="game.html?id=' + encodeURIComponent(game.id) + '">' +
        ui.thumb(game, stats) +
        '<div>' +
          '<h3>' + util.escape(game.title) + '</h3>' +
          '<p>' + util.escape(creator.name) + '</p>' +
          '<p>プレイ ' + util.count(stats.plays || 0) + '回' +
            '<span class="dot"></span>' + util.escape(util.since(game.publishedAt)) + '</p>' +
        '</div>' +
      '</a>';
    },

    grid: function (games, stats, opts) {
      opts = opts || {};
      if (!games.length) {
        return '<div class="empty">' +
          '<strong>' + util.escape(opts.emptyTitle || 'まだ何もありません') + '</strong>' +
          '<p>' + util.escape(opts.emptyBody || '') + '</p>' +
        '</div>';
      }
      return '<div class="grid">' + games.map(function (g) {
        return ui.card(g, stats[g.id]);
      }).join('') + '</div>';
    },

    toast: function (message) {
      var el = document.querySelector('.toast');
      if (!el) {
        el = document.createElement('div');
        el.className = 'toast';
        el.setAttribute('role', 'status');
        document.body.appendChild(el);
      }
      el.textContent = message;
      /* 直前のクラス削除を反映させてからでないと、連続表示でアニメーションが出ない */
      el.classList.remove('show');
      void el.offsetWidth;
      el.classList.add('show');
      clearTimeout(el._timer);
      el._timer = setTimeout(function () { el.classList.remove('show'); }, 2200);
    },

    /** 「404」的な状況で使う。ページ本体を差し替える */
    notFound: function (root, message) {
      root.innerHTML = '<div class="empty">' +
        '<strong>' + util.escape(message || '見つかりませんでした') + '</strong>' +
        '<p><a class="btn" href="index.html">ホームにもどる</a></p>' +
      '</div>';
    }
  };

  applyTheme(currentTheme());

  NS.util = util;
  NS.data = data;
  NS.ui = ui;
})();
