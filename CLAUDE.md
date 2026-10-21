# ⭐ジブリ情報局⭐ SNS制作メモ

ジブリ情報を発信する TikTok アカウント（Instagram ではなく TikTok がメイン）の画像・動画を作るリポジトリ。
ユーザーへの返答・画像内の文字はすべて日本語。

## 最初にやること（新しいセッション）
1. `bash ghibli-toolkit/setup.sh <作業フォルダ>`（作業フォルダはスクラッチパッド推奨）
   - フォント・切り抜きモデル・ジブリ公式場面写真をダウンロードし、`ghibli-toolkit/lib/*.py` をパス置換してコピーする
2. 効果音ラボの音は再配布不可なので、必要になったら https://soundeffect-lab.info/ から `labsfx/` に取得（リポジトリに入れない）
3. VOICEVOX は docker で起動：`dockerd &` → `docker run -d --rm --name vv -p 50021:50021 voicevox/voicevox_engine:cpu-latest`（urllib は `ProxyHandler({})` で接続）

## 共通ルール
- 画面は TikTok の 9:16（1080×1920）。右側ボタン・下の説明文エリアに大事な要素を置かない（通常ページは全体を左に40px寄せる `shifted`／DX=40。サムネは中央そろえ）
- 背景：緑の方眼 `ghibli-toolkit/assets/bg_grid.jpg`（ほぼ全投稿で使用）
- 最後のページ：フォロー画像 `ghibli-toolkit/assets/follow.jpg`
- 文字：丸ゴシック太字（M PLUS Rounded 1c 800/900、`kh2.py` の `text`/`pill`）。白フチ付き。見出しは緑、強調はオレンジや赤の帯（pill）
- サムネの見出しの型：「＼○○で買える／」小さめ黒＋大きい緑文字＋オレンジの帯（例：キーホルダーまとめ vol.2）
- けいふぉんとは傾けない
- キャラ・グッズは切り抜いて白フチのステッカーにして散りばめる（`cutout.py`=アニメキャラ、`biref.py`=商品・写真）
  - その投稿で紹介している作品のキャラを使う
  - 文字やカードと重なるときはステッカーを後ろに
- ジブリの場面写真は公式 https://www.ghibli.jp/gallery/{作品}{番号}.jpg を使用（© Studio Ghibli を表記）
  - 縦長の枠に入れるときは、キャラや見せたいものが切れないよう切り取り位置を作品ごとに調整する
- 実在の場所・町の写真：Wikimedia Commons の CC0 / CC BY / パブリックドメインを使う（CC BY-SA は避ける）。撮影者とライセンスを各画像の下に表記。景観がよく、アニメの場面と似た構図のものを選ぶ
- 公式サイトの商品画像は「無断転載禁止」の表記があるか確認してから使う

## 動画（ナレーション付き）
- 声：VOICEVOX 青山龍星（speaker 13）、speedScale 1.15、無音カット
- 効果音：効果音ラボのクイズ・バラエティ系。「ジャン／パン」は使わない
- ジェットカット。字幕は画面の真ん中に小さめ（白文字＋黒フチ）
- iPhone の HDR 動画は tonemap して SDR に変換してから使う
- 最後はフォロー画像＋「ジブリの最新情報を発信中。フォローしてね！」

## 進め方
- まず台本・構成・候補を出して確認をもらってから作る
- 説明欄は短く（基本3行）。写真クレジットが長い場合は「各画像に記載」と書く
- 完成したらコミット＆プッシュし、画像は投稿順に送る（まとめて保存したいときは zip）
- Claude の使用量を使いすぎないよう、手順は最小限に

## 参考になる過去作
- 商品まとめ（4つずつ）：`ghibli-keyholder/`、`ghibli-kinro-saga/`
- 1ページ1商品：`ghibli-majo-goods/`
- 1作品1ページ＋キャッチコピー：`ghibli-kids5/`
- 4枚の写真を田の字＋中央カード：`ghibli-abroad/`、`ghibli-japan/`
- まとめカルーセル（情報系）：`ghibli-imax/`
- ナレーション動画：`majo-sainou/`、`ghibli-donguri-vlog/`、`ghibli-zenmap/`
