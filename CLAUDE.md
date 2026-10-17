# このリポジトリについて

ジブリ作品の YouTube ショート／TikTok／YouTube 横動画（都市伝説・考察）を Python で自動生成している。

- 動画の企画・台本・サムネを考えるときは、まず `docs/youtube_growth_2026.md`（YouTube の伸ばし方と収益化ポリシーの調査メモ）を読むこと。
  特に「画像スライドショー＋合成音声」は量産型（inauthentic content）と見なされるリスクがあるので、毎回独自の考察・ストーリー・編集を入れる。
- 雑学は映画の中の描写に基づくものにする（制作の裏話より作中の話）。雑学の羅列ではなく 1 本 1 ストーリーにする。
- ナレーションは VOICEVOX（localhost:50021）。読みは audio_query の kana で確認し、間違う語は読み用テキストを書き換える。
- 横動画：`horiz-video/`（kaonashi.py＝描画・音の部品、kaonashi_full.py＝本編、kaonashi_short.py＝誘導ショート）。
- BGM（魔王魂）と効果音ラボの音源は再配布しないので git に入れない（horiz-video/bgm/、chihiro-video/sfx/）。
