/*
 * プレイ画面。ゲームを iframe で全画面に出すだけの薄い枠。
 *
 * 上のバーは3秒で引っ込みます。ゲーム側がタッチや視点操作に画面全体を使うので、
 * 邪魔をしないのが第一。画面の上端に触れると戻ってきます。
 */
(function () {
  'use strict';

  var NS = window.ASOBIBA;
  var util = NS.util, data = NS.data, ui = NS.ui, store = NS.store;

  var root = document.getElementById('player');
  var id = util.param('id');
  var barTimer = null;
  var blobUrl = null;

  data.load().then(function () {
    var game = data.game(id);
    if (!game) {
      document.body.className = '';
      root.className = 'page';
      ui.header();
      ui.notFound(root, 'そのゲームは見つかりませんでした');
      return;
    }
    document.title = game.title + ' — あそびば';
    return store.stats(game.id).then(function (stats) {
      mount(game, stats);
    });
  });

  function sourceFor(game) {
    if (game.playUrl) return { src: game.playUrl, sandbox: null };

    /* この端末に置いた投稿。あそびば側のデータを触れないよう、
       allow-same-origin を付けずに別オリジン扱いで動かす。 */
    blobUrl = URL.createObjectURL(new Blob([game.localHtml || ''], { type: 'text/html' }));
    return { src: blobUrl, sandbox: 'allow-scripts allow-pointer-lock allow-modals allow-forms allow-popups' };
  }

  function mount(game, stats) {
    var source = sourceFor(game);

    root.innerHTML =
      '<div class="player-bar" id="bar">' +
        '<button class="btn js-back" type="button">' + ui.icons.back + '<span>もどる</span></button>' +
        '<span class="title">' + util.escape(game.title) + '</span>' +
        '<span class="spacer"></span>' +
        '<button class="btn js-like' + (stats.liked ? ' is-on' : '') + '" type="button" aria-pressed="' + stats.liked + '">' +
          (stats.liked ? ui.icons.heartFull : ui.icons.heart) + '<span>いいね</span>' +
        '</button>' +
        '<button class="btn btn-icon js-full" type="button" aria-label="全画面にする">' + ui.icons.expand + '</button>' +
      '</div>' +
      '<iframe id="frame" title="' + util.escape(game.title) + '"' +
        (source.sandbox ? ' sandbox="' + source.sandbox + '"' : '') +
        ' allow="fullscreen; autoplay; gamepad; accelerometer; gyroscope"' +
        ' src="' + util.escape(source.src) + '"></iframe>';

    if (game.orientation === 'landscape') maybeRotateHint();

    wire(game);
    store.recordPlay(game.id);
    scheduleHide();
  }

  /* 横画面向けのゲームを縦で開いたときだけ、最初に案内を出す */
  function maybeRotateHint() {
    var portrait = window.innerHeight > window.innerWidth;
    var small = Math.min(window.innerWidth, window.innerHeight) < 820;
    if (!portrait || !small) return;

    var hint = document.createElement('div');
    hint.className = 'rotate-hint';
    hint.innerHTML =
      ui.icons.rotate +
      '<strong>横向きにしてください</strong>' +
      '<p>このゲームは横画面用に作られています。端末を横にすると操作しやすくなります。</p>' +
      '<button class="btn" type="button">このまま遊ぶ</button>';
    root.appendChild(hint);

    var close = function () { hint.remove(); window.removeEventListener('resize', onResize); };
    var onResize = function () { if (window.innerWidth > window.innerHeight) close(); };

    hint.querySelector('button').addEventListener('click', close);
    window.addEventListener('resize', onResize);
  }

  function bar() { return document.getElementById('bar'); }

  function showBar() {
    bar().classList.remove('hidden');
    scheduleHide();
  }

  function scheduleHide() {
    clearTimeout(barTimer);
    barTimer = setTimeout(function () {
      var b = bar();
      if (b && !b.contains(document.activeElement)) b.classList.add('hidden');
    }, 3000);
  }

  function wire(game) {
    var b = bar();

    b.querySelector('.js-back').addEventListener('click', function () {
      if (document.referrer && document.referrer.indexOf(window.location.origin) === 0) {
        window.history.back();
      } else {
        window.location.href = 'game.html?id=' + encodeURIComponent(game.id);
      }
    });

    var like = b.querySelector('.js-like');
    like.addEventListener('click', function () {
      store.toggleLike(game.id).then(function (r) {
        like.classList.toggle('is-on', r.liked);
        like.setAttribute('aria-pressed', String(r.liked));
        like.innerHTML = (r.liked ? ui.icons.heartFull : ui.icons.heart) + '<span>いいね</span>';
        ui.toast(r.liked ? 'いいねしました' : 'いいねを取り消しました');
        showBar();
      });
    });

    b.querySelector('.js-full').addEventListener('click', function () {
      var el = document.documentElement;
      if (document.fullscreenElement) {
        document.exitFullscreen();
        return;
      }
      var req = el.requestFullscreen || el.webkitRequestFullscreen;
      if (!req) {
        ui.toast('この端末では全画面にできません');
        return;
      }
      Promise.resolve(req.call(el)).then(function () {
        /* 横画面用のゲームなら、全画面のついでに向きも固定してみる。
           対応していない端末では例外になるだけなので握りつぶす。 */
        if (game.orientation === 'landscape' && screen.orientation && screen.orientation.lock) {
          try { screen.orientation.lock('landscape').catch(function () {}); } catch (e) {}
        }
      }).catch(function () {
        ui.toast('全画面にできませんでした');
      });
    });

    /* バーの出し入れ。ゲームの操作を邪魔しないよう、上端の帯だけで反応する */
    window.addEventListener('mousemove', function (e) {
      if (e.clientY < 80) showBar();
    });
    window.addEventListener('touchstart', function (e) {
      var y = e.touches && e.touches[0] ? e.touches[0].clientY : 999;
      if (y < 80) showBar();
    }, { passive: true });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') showBar();
    });
    b.addEventListener('mouseenter', showBar);
    b.addEventListener('focusin', showBar);
  }

  window.addEventListener('pagehide', function () {
    if (blobUrl) URL.revokeObjectURL(blobUrl);
  });
})();
