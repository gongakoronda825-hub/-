/*
 * ゲーム詳細ページ。遊ぶ前に見る画面。
 * ここではプレイ数を増やしません。数えるのは play.html で実際に起動したときだけです。
 */
(function () {
  'use strict';

  var NS = window.ASOBIBA;
  var util = NS.util, data = NS.data, ui = NS.ui, store = NS.store;

  var id = util.param('id');
  var main = document.getElementById('main');

  ui.header();

  data.load().then(function () {
    var game = data.game(id);
    if (!game) {
      ui.notFound(main, 'そのゲームは見つかりませんでした');
      ui.footer();
      return;
    }

    document.title = game.title + ' — あそびば';
    var creator = data.creator(game.creatorId) || { name: '', bio: '', links: [] };

    return Promise.all([
      store.stats(game.id),
      store.isFollowing(creator.id),
      store.followerCount(creator.id)
    ]).then(function (res) {
      render(game, creator, res[0], res[1], res[2]);
    });
  });

  function render(game, creator, stats, following, followers) {
    var related = data.related(game.id, 6);
    var playHref = 'play.html?id=' + encodeURIComponent(game.id);

    main.innerHTML =
      '<div class="watch">' +
        '<div>' +
          '<a class="stage" href="' + playHref + '">' +
            (game.thumbnail
              ? '<img src="' + util.escape(game.thumbnail) + '" alt="">'
              : '<div class="thumb-fallback">' + util.escape(game.title.slice(0, 1)) + '</div>') +
            '<span class="stage-overlay">' +
              '<span class="btn btn-primary btn-lg">' + ui.icons.play + 'このゲームを遊ぶ</span>' +
              '<p>ブラウザでそのまま動きます。インストールは要りません。</p>' +
            '</span>' +
          '</a>' +

          '<h1>' + util.escape(game.title) + '</h1>' +
          (game.tagline ? '<p class="watch-tagline">' + util.escape(game.tagline) + '</p>' : '') +

          '<div class="watch-actions">' +
            '<span class="stat">プレイ ' + util.count(stats.plays) + '回' +
              '<span class="dot"></span>' + util.escape(util.date(game.publishedAt)) + '公開</span>' +
            '<button class="btn js-like' + (stats.liked ? ' is-on' : '') + '" type="button" aria-pressed="' + stats.liked + '">' +
              (stats.liked ? ui.icons.heartFull : ui.icons.heart) +
              '<span class="js-like-label">' + (stats.liked ? 'いいね済み' : 'いいね') + '</span>' +
            '</button>' +
            '<button class="btn js-share" type="button">' + ui.icons.share + '共有</button>' +
            '<a class="btn btn-primary" href="' + playHref + '">' + ui.icons.play + '遊ぶ</a>' +
          '</div>' +

          '<div class="creator-row">' +
            '<a class="avatar" href="creator.html?id=' + encodeURIComponent(creator.id) + '" aria-hidden="true">' +
              util.escape(String(creator.name || '?').slice(0, 1)) + '</a>' +
            '<div>' +
              '<a class="name" href="creator.html?id=' + encodeURIComponent(creator.id) + '">' +
                util.escape(creator.name) + '</a>' +
              '<div class="sub js-follower-count">フォロワー ' + util.count(followers) + '人' +
                '<span class="dot"></span>' + data.gamesByCreator(creator.id).length + '本</div>' +
            '</div>' +
            (creator.local ? '' :
              '<button class="btn btn-follow js-follow' + (following ? ' is-on' : '') + '" type="button" aria-pressed="' + following + '">' +
                (following ? 'フォロー中' : 'フォローする') +
              '</button>') +
          '</div>' +

          '<div class="panel">' +
            '<div class="js-desc' + (game.description.length > 160 ? ' desc-collapsed' : '') + '">' +
              game.description.split('\n\n').map(function (p) {
                return '<p>' + util.escape(p) + '</p>';
              }).join('') +
            '</div>' +
            (game.description.length > 160
              ? '<button class="desc-toggle js-desc-toggle" type="button">もっと読む</button>' : '') +
            '<div class="taglist">' +
              (game.tags || []).map(function (t) {
                return '<a href="index.html?tag=' + encodeURIComponent(t) + '">#' + util.escape(t) + '</a>';
              }).join('') +
            '</div>' +
          '</div>' +

          (game.controls && game.controls.length ?
            '<h2 class="section-title">操作</h2>' +
            '<div class="panel"><table class="controls-table"><tbody>' +
              game.controls.map(function (c) {
                return '<tr><th scope="row">' + util.escape(c.device) + '</th>' +
                  '<td>' + util.escape(c.text) + '</td></tr>';
              }).join('') +
            '</tbody></table></div>' : '') +
        '</div>' +

        '<aside>' +
          '<h2 class="section-title" style="margin-top:0">この作品について</h2>' +
          '<div class="panel"><dl class="facts">' +
            '<div><dt>カテゴリ</dt><dd>' +
              (game.categories || []).map(function (c) {
                return '<a href="index.html?category=' + encodeURIComponent(c) + '">' +
                  util.escape(data.categoryLabel(c)) + '</a>';
              }).join('、') + '</dd></div>' +
            (game.playtime ? '<div><dt>プレイ時間</dt><dd>' + util.escape(game.playtime) + '</dd></div>' : '') +
            '<div><dt>向き</dt><dd>' + orientationLabel(game.orientation) + '</dd></div>' +
            '<div><dt>更新</dt><dd>' + util.escape(util.since(game.updatedAt || game.publishedAt)) + '</dd></div>' +
            (game.sourceUrl
              ? '<div><dt>ソース</dt><dd><a href="' + util.escape(game.sourceUrl) + '">GitHub で見る</a></dd></div>'
              : '') +
          '</dl></div>' +

          (related.length ? '<h2 class="section-title">次に遊ぶ</h2><div class="side-list" id="related"></div>' : '') +
        '</aside>' +
      '</div>';

    if (related.length) {
      store.statsFor(related.map(function (g) { return g.id; })).then(function (map) {
        document.getElementById('related').innerHTML = related.map(function (g) {
          return ui.sideCard(g, map[g.id]);
        }).join('');
      });
    }

    wire(game, creator);
    ui.footer();
  }

  function orientationLabel(o) {
    if (o === 'landscape') return '横画面（スマホは横向きに）';
    if (o === 'portrait') return '縦画面';
    return '縦でも横でも';
  }

  function wire(game, creator) {
    var like = main.querySelector('.js-like');
    like.addEventListener('click', function () {
      store.toggleLike(game.id).then(function (r) {
        like.classList.toggle('is-on', r.liked);
        like.setAttribute('aria-pressed', String(r.liked));
        like.innerHTML = (r.liked ? ui.icons.heartFull : ui.icons.heart) +
          '<span class="js-like-label">' + (r.liked ? 'いいね済み' : 'いいね') + '</span>';
        ui.toast(r.liked ? 'いいねしました' : 'いいねを取り消しました');
      });
    });

    var follow = main.querySelector('.js-follow');
    if (follow) {
      follow.addEventListener('click', function () {
        store.toggleFollow(creator.id).then(function (r) {
          follow.classList.toggle('is-on', r.following);
          follow.setAttribute('aria-pressed', String(r.following));
          follow.textContent = r.following ? 'フォロー中' : 'フォローする';
          ui.toast(r.following ? creator.name + ' をフォローしました' : 'フォローを解除しました');

          store.followerCount(creator.id).then(function (n) {
            var el = main.querySelector('.js-follower-count');
            el.innerHTML = el.innerHTML.replace(
              /フォロワー [^<]*人/, 'フォロワー ' + util.count(n) + '人'
            );
          });
        });
      });
    }

    var toggle = main.querySelector('.js-desc-toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var box = main.querySelector('.js-desc');
        var open = box.classList.toggle('desc-collapsed');
        toggle.textContent = open ? 'もっと読む' : '閉じる';
      });
    }

    main.querySelector('.js-share').addEventListener('click', function () {
      var url = window.location.href;
      var payload = { title: game.title + ' — あそびば', text: game.tagline, url: url };

      if (navigator.share) {
        navigator.share(payload).catch(function () { /* 閉じただけなので何もしない */ });
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () {
          ui.toast('リンクをコピーしました');
        }, function () {
          ui.toast(url);
        });
        return;
      }
      ui.toast(url);
    });
  }
})();
