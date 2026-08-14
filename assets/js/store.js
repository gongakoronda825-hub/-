/*
 * 反応（プレイ数・いいね・フォロー）と、この端末に置いた投稿の保管庫。
 *
 * いまの保存先は localStorage だけです。ただし呼び出し側からは全部 Promise を
 * 返す非同期APIに見えるようにしてあります。将来サーバーを立てたときに、この
 * ファイルの中身を fetch に差し替えるだけで済むようにするためです。
 * 画面側のコードは一切 localStorage を直接触りません。
 */
(function () {
  'use strict';

  var NS = (window.ASOBIBA = window.ASOBIBA || {});

  var KEY = 'asobiba.state.v1';
  var GAMES_KEY = 'asobiba.localgames.v1';
  var PLAY_COOLDOWN_MS = 30 * 60 * 1000; // 同じゲームを開き直しても30分は数えない
  var HISTORY_MAX = 24;
  var UPLOAD_MAX_BYTES = 2.5 * 1024 * 1024;

  var memory = null; // localStorage が使えない環境（プライベートモード等）の退避先

  function blank() {
    return { likes: {}, plays: {}, follows: {}, history: [] };
  }

  function read(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return memory && memory[key] ? memory[key] : fallback;
    }
  }

  function write(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      memory = memory || {};
      memory[key] = value;
      return false;
    }
  }

  function state() {
    var s = read(KEY, null);
    if (!s || typeof s !== 'object') s = blank();
    s.likes = s.likes || {};
    s.plays = s.plays || {};
    s.follows = s.follows || {};
    s.history = Array.isArray(s.history) ? s.history : [];
    return s;
  }

  function save(s) { return write(KEY, s); }

  function resolve(value) { return Promise.resolve(value); }

  var store = {
    /* -------------------------------------------------------- 統計 */

    /** 1件ぶんの反応をまとめて返す */
    stats: function (gameId) {
      var s = state();
      var play = s.plays[gameId] || { count: 0, last: 0 };
      return resolve({
        plays: play.count,
        lastPlayedAt: play.last,
        likes: s.likes[gameId] ? 1 : 0,
        liked: !!s.likes[gameId]
      });
    },

    /** 複数件を一度に。フィードの描画で使う */
    statsFor: function (gameIds) {
      var s = state();
      var out = {};
      gameIds.forEach(function (id) {
        var play = s.plays[id] || { count: 0, last: 0 };
        out[id] = {
          plays: play.count,
          lastPlayedAt: play.last,
          likes: s.likes[id] ? 1 : 0,
          liked: !!s.likes[id]
        };
      });
      return resolve(out);
    },

    /**
     * プレイを1回ぶん数える。連続で開き直したぶんは数えない。
     * 数えたときだけ counted: true を返す。
     */
    recordPlay: function (gameId) {
      var s = state();
      var now = Date.now();
      var play = s.plays[gameId] || { count: 0, last: 0 };
      var counted = now - play.last > PLAY_COOLDOWN_MS;

      if (counted) play.count += 1;
      play.last = now;
      s.plays[gameId] = play;

      s.history = [{ id: gameId, at: now }].concat(
        s.history.filter(function (h) { return h.id !== gameId; })
      ).slice(0, HISTORY_MAX);

      save(s);
      return resolve({ counted: counted, plays: play.count });
    },

    toggleLike: function (gameId) {
      var s = state();
      var liked = !s.likes[gameId];
      if (liked) s.likes[gameId] = Date.now();
      else delete s.likes[gameId];
      save(s);
      return resolve({ liked: liked });
    },

    likedGameIds: function () {
      var s = state();
      return resolve(Object.keys(s.likes).sort(function (a, b) {
        return s.likes[b] - s.likes[a];
      }));
    },

    /* ------------------------------------------------------ フォロー */

    isFollowing: function (creatorId) {
      return resolve(!!state().follows[creatorId]);
    },

    toggleFollow: function (creatorId) {
      var s = state();
      var following = !s.follows[creatorId];
      if (following) s.follows[creatorId] = Date.now();
      else delete s.follows[creatorId];
      save(s);
      return resolve({ following: following });
    },

    /** いまのところ「この端末がフォローしているか」の 0 か 1 */
    followerCount: function (creatorId) {
      return resolve(state().follows[creatorId] ? 1 : 0);
    },

    followedCreatorIds: function () {
      return resolve(Object.keys(state().follows));
    },

    /* -------------------------------------------------- 最近遊んだ */

    history: function (limit) {
      var h = state().history;
      return resolve(typeof limit === 'number' ? h.slice(0, limit) : h.slice());
    },

    clearHistory: function () {
      var s = state();
      s.history = [];
      save(s);
      return resolve(true);
    },

    /* ------------------------------------------ この端末に置いた投稿 */

    localGames: function () {
      var list = read(GAMES_KEY, []);
      return resolve(Array.isArray(list) ? list : []);
    },

    /**
     * 投稿ページから呼ぶ。html は丸ごと文字列で預かる。
     * localStorage の容量に収まらないときは saved:false を返し、
     * 画面側で「配置手順だけ使ってください」と案内する。
     */
    saveLocalGame: function (game) {
      if (game.html && game.html.length > UPLOAD_MAX_BYTES) {
        return resolve({ saved: false, reason: 'too-large', limit: UPLOAD_MAX_BYTES });
      }
      var list = read(GAMES_KEY, []);
      if (!Array.isArray(list)) list = [];
      list = list.filter(function (g) { return g.id !== game.id; });
      list.unshift(game);

      if (!write(GAMES_KEY, list)) {
        return resolve({ saved: false, reason: 'quota' });
      }
      return resolve({ saved: true });
    },

    removeLocalGame: function (id) {
      var list = read(GAMES_KEY, []);
      if (!Array.isArray(list)) list = [];
      write(GAMES_KEY, list.filter(function (g) { return g.id !== id; }));
      return resolve(true);
    },

    /** この端末の記録を全部消す */
    reset: function () {
      try {
        window.localStorage.removeItem(KEY);
        window.localStorage.removeItem(GAMES_KEY);
      } catch (e) { /* 使えない環境なら消すものも無い */ }
      memory = null;
      return resolve(true);
    }
  };

  NS.store = store;
})();
