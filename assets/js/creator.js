/*
 * クリエイターページ。YouTube でいうチャンネル。
 */
(function () {
  'use strict';

  var NS = window.ASOBIBA;
  var util = NS.util, data = NS.data, ui = NS.ui, store = NS.store;

  var id = util.param('id');
  var main = document.getElementById('main');

  ui.header();

  data.load().then(function () {
    var creator = data.creator(id);
    if (!creator) {
      ui.notFound(main, 'そのクリエイターは見つかりませんでした');
      ui.footer();
      return;
    }

    document.title = creator.name + ' — あそびば';
    var games = data.gamesByCreator(creator.id);

    return Promise.all([
      store.statsFor(games.map(function (g) { return g.id; })),
      store.isFollowing(creator.id),
      store.followerCount(creator.id)
    ]).then(function (res) {
      render(creator, games, res[0], res[1], res[2]);
    });
  });

  function render(creator, games, stats, following, followers) {
    var totalPlays = games.reduce(function (sum, g) {
      return sum + ((stats[g.id] || {}).plays || 0);
    }, 0);

    main.innerHTML =
      '<div class="banner"></div>' +
      '<div class="creator-hero">' +
        '<span class="avatar avatar-lg" aria-hidden="true">' +
          util.escape(String(creator.name || '?').slice(0, 1)) + '</span>' +
        '<div>' +
          '<h1>' + util.escape(creator.name) + '</h1>' +
          '<div class="stats">' +
            'フォロワー ' + util.count(followers) + '人' +
            '<span class="dot"></span>' + games.length + '本' +
            '<span class="dot"></span>合計 ' + util.count(totalPlays) + 'プレイ' +
          '</div>' +
          (creator.bio ? '<p class="bio">' + util.escape(creator.bio) + '</p>' : '') +
        '</div>' +
        '<div class="actions">' +
          (creator.links || []).map(function (l) {
            return '<a class="btn" href="' + util.escape(l.url) + '" rel="noopener">' +
              util.escape(l.label) + '</a>';
          }).join('') +
          (creator.local ? '' :
            '<button class="btn btn-primary js-follow' + (following ? ' btn-follow is-on' : '') + '" type="button" aria-pressed="' + following + '">' +
              (following ? 'フォロー中' : 'フォローする') +
            '</button>') +
        '</div>' +
      '</div>' +

      '<h2 class="section-title">作品</h2>' +
      ui.grid(games, stats, {
        emptyTitle: 'まだ作品がありません',
        emptyBody: creator.local ? '投稿ページからゲームを追加できます。' : ''
      });

    var follow = main.querySelector('.js-follow');
    if (follow) {
      follow.addEventListener('click', function () {
        store.toggleFollow(creator.id).then(function (r) {
          follow.classList.toggle('is-on', r.following);
          follow.classList.toggle('btn-follow', r.following);
          follow.classList.toggle('btn-primary', !r.following);
          follow.setAttribute('aria-pressed', String(r.following));
          follow.textContent = r.following ? 'フォロー中' : 'フォローする';
          ui.toast(r.following ? creator.name + ' をフォローしました' : 'フォローを解除しました');
          /* 人数表示もその場で合わせる */
          store.followerCount(creator.id).then(function (n) {
            var stats = main.querySelector('.stats');
            stats.innerHTML = stats.innerHTML.replace(
              /フォロワー [^<]*人/, 'フォロワー ' + util.count(n) + '人'
            );
          });
        });
      });
    }

    ui.footer();
  }
})();
