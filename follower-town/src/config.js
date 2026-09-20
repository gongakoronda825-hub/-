/*
 * 街の設定。
 *
 * ここの POPULATION を変えるだけで街の時代が変わる、という構造にしてある。
 *   FT.config.POPULATION = 0      → 人類誕生前（恐竜時代）
 *   FT.config.POPULATION = 1      → 縄文
 *   FT.config.POPULATION = 3000   → 江戸
 * 将来 TikTok のフォロワー数を入れる場所も FOLLOWERS として用意しておく。
 * （今回は外部APIに繋がない。フォロワー = 人口 として扱う）
 *
 * 動作確認用に ?pop=100&followers=100&seed=7 で上書きできる。
 */
(function (global) {
  'use strict';
  const FT = (global.FT = global.FT || {});

  const config = {
    // ── 街の状態 ────────────────────────────────
    FOLLOWERS: 0,
    POPULATION: 0,

    // ── 見た目 ─────────────────────────────────
    SEED: 20260920, // 地形の乱数シード。変えると別の土地になる
    // 内部解像度（この解像度で描いて、画面いっぱいに整数倍っぽく引き伸ばす）
    BASE_SHORT_SIDE: 240, // 画面の短辺に対応するドット数
    BASE_LONG_SIDE_MAX: 560, // 長辺の上限（横長の画面で広がりすぎないように）

    // ── 生き物の数（画面を恐竜だらけにしない） ──────
    HERD: { sauropod: 2, stego: 2, raptor: 4 },
    PTERO_INTERVAL: [14, 26], // 翼竜が横切る間隔（秒）

    // ── カメラ ─────────────────────────────────
    CAMERA_DRIFT_X: 26, // ゆっくりした横揺れ幅(px)
    CAMERA_DRIFT_Y: 13,
    CAMERA_PERIOD_X: 96, // 秒。動画で酔わない速さにする
    CAMERA_PERIOD_Y: 71,
  };

  const q = new URLSearchParams(global.location ? global.location.search : '');
  const num = (key, fallback) => {
    const v = Number(q.get(key));
    return q.has(key) && Number.isFinite(v) ? v : fallback;
  };
  config.POPULATION = Math.max(0, Math.floor(num('pop', config.POPULATION)));
  config.FOLLOWERS = Math.max(0, Math.floor(num('followers', config.POPULATION)));
  config.SEED = Math.floor(num('seed', config.SEED));

  FT.config = config;
})(window);
