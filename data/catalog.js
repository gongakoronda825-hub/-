/*
 * 掲載ゲームのカタログ。
 *
 * このファイルが、サイトに何が並ぶかの唯一の情報源です。ゲームを増やすときは
 * games[] に1件足すだけで、フィード・検索・カテゴリ・おすすめ・クリエイター
 * ページのすべてに反映されます。追加手順は README を参照。
 *
 * fetch ではなく素の <script> で読み込んでいるのは、file:// で直接開いても
 * 動くようにするためです（file:// では fetch も ES module も CORS で落ちる）。
 *
 * 数字（プレイ数・いいね・フォロワー）はここには持たせません。実際に遊ばれた
 * 回数だけを閲覧者の端末に記録して数えます。初期値の水増しはしない方針です。
 */
window.ASOBIBA = window.ASOBIBA || {};

window.ASOBIBA.site = {
  name: 'あそびば',
  tagline: 'つくったゲームを、すぐ遊んでもらえる場所。',
  repoUrl: 'https://github.com/gongakoronda825-hub/-'
};

window.ASOBIBA.catalog = {
  /* 表示順がそのままカテゴリチップの並び順になります */
  categories: [
    { id: 'all', label: 'すべて' },
    { id: 'action', label: 'アクション' },
    { id: 'adventure', label: 'ぼうけん' },
    { id: 'story', label: 'ものがたり' },
    { id: 'puzzle', label: 'パズル' },
    { id: 'sandbox', label: 'サンドボックス' },
    { id: '3d', label: '3D' },
    { id: 'pixel', label: 'ドット絵' }
  ],

  creators: [
    {
      id: 'gongakoronda825',
      name: 'gongakoronda825',
      bio: 'ブラウザだけで遊べるゲームを作っています。インストールも登録も要らないものだけ。',
      accent: '#ff4d6a',
      joinedAt: '2026-08-10',
      links: [
        { label: 'GitHub', url: 'https://github.com/gongakoronda825-hub' }
      ]
    }
  ],

  games: [
    {
      id: 'ultimate-choice',
      title: '究極の選択',
      tagline: '悪魔に取引を持ちかけられる、ドット絵RPG風の1シーン。',
      description:
        '導入はギャグ、選択のあとはシリアスに落ちる。その温度差が主題です。結末は2つ。\n\n' +
        '256×224 のバッファに Canvas 2D で描いた、外部ライブラリなしの1ファイル完結。' +
        'キャラクターは「1文字 = 1ドット」の2次元配列から起こしていて、洞窟や夜景の背景は' +
        'シード付き擬似乱数で毎回その場で生成しています。効果音も Web Audio でつくった音です。\n\n' +
        '台詞の表示速度は行ごとに変えてあります。ギャグ部分は速く、終盤の独白はゆっくり、' +
        '最後の1行だけは極端に遅い。片方のルートには1.5秒だけ何も起きない沈黙があって、' +
        'そこがこの作品の中心です。',
      creatorId: 'gongakoronda825',
      categories: ['story', 'adventure', 'pixel'],
      tags: ['ノベル', 'RPG風', 'ドット絵', '選択肢', 'ショート'],
      playUrl: 'games/ultimate-choice/index.html',
      sourceUrl: 'https://github.com/gongakoronda825-hub/-/blob/main/games/ultimate-choice/index.html',
      thumbnail: 'assets/img/thumb-ultimate-choice.png',
      orientation: 'any',
      playtime: '5分ほど',
      publishedAt: '2026-08-10',
      updatedAt: '2026-08-10',
      controls: [
        { device: 'スマホ', text: '画面をタップ、または下の ▲ ▼ けってい ボタン' },
        { device: 'PC', text: '↑ ↓ でえらぶ、Z または Enter でけってい' }
      ]
    },
    {
      id: 'block-game',
      title: 'ブロックの世界',
      tagline: '一人称のボクセルゲーム。地形を歩いて、木を切って、ブロックを積む。',
      description:
        'ノイズから生まれた地形を歩きまわる、一人称のサンドボックス。牛と羊がうろついています。\n\n' +
        '世界はチャンク単位で、歩いた先が順に生成されていきます。木を切ってブロックを集め、' +
        '狙った面の隣に積む。ジャンプを2回連打すると飛行に切り替わって、上から地形を眺められます。\n\n' +
        '配信しているのは1枚の HTML だけです。three.js もテクスチャも全部その中に入っていて、' +
        '外部への通信がまったく無いので、ダウンロードしてオフラインで開いても同じように動きます。',
      creatorId: 'gongakoronda825',
      categories: ['sandbox', 'adventure', '3d'],
      tags: ['3D', 'ボクセル', '探索', 'クラフト', '横画面'],
      playUrl: 'block-game/play/index.html',
      sourceUrl: 'https://github.com/gongakoronda825-hub/-/tree/main/block-game',
      thumbnail: 'assets/img/thumb-block-game.jpg',
      orientation: 'landscape',
      playtime: '好きなだけ',
      publishedAt: '2026-08-11',
      updatedAt: '2026-08-12',
      controls: [
        { device: 'スマホ', text: '左下のスティックで移動、右半分をなぞって見まわす。ジャンプを2回連打で飛行' },
        { device: 'PC', text: 'WASD／矢印キーで移動、マウスドラッグで視点、スペースでジャンプ、1〜5 でブロック選択' }
      ]
    }
  ]
};
