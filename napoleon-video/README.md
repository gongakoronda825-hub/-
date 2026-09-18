# 棒人間 雑学ショート (テスト動画)

棒人間が歴史・雑学を1つ紹介する30秒のMP4を、台本から一気通貫で生成します。
ルックは **ノート落書き風** — ルーズリーフの紙に鉛筆で描いた落書き、で統一しています。

- 紙: クリーム色 + 青い罫線 + 左の赤い縦線 + 綴じ穴。繊維と皺のテクスチャ入り
- 線: 黒1色の手描き。震え・太さの揺らぎ・始点終点のはみ出し付き (`sketch_line` / `sketch_ellipse`)
- 色: 強調の2色だけ (黄色マーカー / 赤の色鉛筆)。キャラは黒のみ
- 文字: 手書き風フォント (Zen Kurenaido) を罫線のベースラインに乗せて配置
- 動き: 10fps で描き直す「パラパラ漫画」方式。ステップごとに乱数を引き直すので線が小刻みに揺れる
- 装飾: 丸囲み・マーカー・下線・集中線が、あとから書き足されるように伸びていく
- 転換: 文と文のあいだで**ページをめくる** (左綴じ。紙が回りながら左へ抜け、影が落ちる)
- 図解: セグメント単位で絵を `character` (棒人間) と `figure` (比較図) から選べる

## 使い方

```bash
# 依存: ffmpeg / Pillow / numpy (フォントは fonts/ に同梱)
apt-get install -y ffmpeg
pip3 install pillow numpy

python3 napoleon-video/make_video.py --preview   # 1フレームだけ確認 (output/preview.png)
python3 napoleon-video/make_video.py             # 本番 (output/test_video.mp4)
```

## 構成

| ファイル | 役割 |
| --- | --- |
| `script.py` | 台本。タイトルと「ナレーション文 / 字幕」のセグメント配列 |
| `tts.py` | 音声合成。VOICEVOX → OS標準TTS → 音声なし の順にフォールバック |
| `renderer.py` | 1フレームの描画 (紙・手描き線・キャラ・図解・字幕・装飾・ページめくり) |
| `fetch_fonts.sh` | 手書き風フォントの取得 (fonts/ に同梱済み) |
| `voices/` | ナレーションの音響モデル (mei_normal.htsvoice, CC BY 3.0) |
| `make_video.py` | パイプライン本体 (設定値は先頭の定数) |

解像度・fps・尺・間の取り方は `make_video.py` 冒頭の定数で、紙や筆記具の色・キャラの骨格は
`renderer.py` 冒頭の定数で変更できます。`ANIM_FPS` を上げるとパラパラ感が薄れて滑らかになります。

強調 (丸囲み・マーカー・下線・集中線) は `script.py` の各セグメントの `marks` で、
本文の絵は `art` (`character` / `figure`) で指定します。比較図の目盛りや棒の値は
`renderer.py` の `FIG_*` 定数にあります。ページめくりの長さは `make_video.py` の `TURN_DUR`。

## ナレーション音声

上から順に試して、使えたものを採用します。

1. **VOICEVOX ENGINE** — `docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest`
   を起動しておくと自動で使われます (`VOICEVOX_URL` / `VOICEVOX_SPEAKER` で変更可)。
   **VOICEVOXで生成した音声を公開する場合は、各キャラクターの利用規約に沿ったクレジット表記が必要です**
   (例: `VOICEVOX:ずんだもん`)。
2. **OS標準の日本語TTS** — macOS `say -v Kyoko` / Windows SAPI / Linux `open_jtalk`
   (`apt-get install open-jtalk open-jtalk-mecab-naist-jdic`)。
   Linux では `voices/mei_normal.htsvoice` (女性声) を自動で使います。システムの
   htsvoice を使いたい場合は `OPEN_JTALK_VOICE` に絶対パスを指定してください。
   明瞭度・ピッチ・音量は `tts.py` の `OPEN_JTALK_ARGS` で調整できます。
   **同梱の HTS Voice "Mei" は CC BY 3.0 です。この声で作った動画を公開する場合は
   `HTS Voice "Mei" (C) 2009-2013 Nagoya Institute of Technology / CC BY 3.0` の表示が必要です**
   (原文は `voices/LICENSE_mei_normal.htsvoice`)。
3. **音声なし** — 字幕だけで成立するようにタイミングを文字数比で割り当てます

話速はナレーション合計が30秒に収まるよう自動調整されます。合成後は ffmpeg で
ハイパス・イコライザ・コンプレッサをかけ、こもりを取ってから音量をそろえています
(`make_video.py` の `polish_track`)。

## BGM

リポジトリのルート直下に royalty-free の音声ファイル (`*.mp3` / `*.wav` など、ファイル名に `bgm` を
含むものを優先) を置くと、小音量 (10%) でミックスされます。無ければスキップします。
