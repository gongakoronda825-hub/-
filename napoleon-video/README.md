# 棒人間 雑学ショート (テスト動画)

棒人間が歴史・雑学を1つ紹介する30秒のMP4を、台本から一気通貫で生成します。

## 使い方

```bash
# 依存: ffmpeg / Pillow / numpy / 日本語フォント
apt-get install -y ffmpeg fonts-noto-cjk
pip3 install pillow numpy

python3 napoleon-video/make_video.py --preview   # 1フレームだけ確認 (output/preview.png)
python3 napoleon-video/make_video.py             # 本番 (output/test_video.mp4)
```

## 構成

| ファイル | 役割 |
| --- | --- |
| `script.py` | 台本。タイトルと「ナレーション文 / 字幕」のセグメント配列 |
| `tts.py` | 音声合成。VOICEVOX → OS標準TTS → 音声なし の順にフォールバック |
| `renderer.py` | 1フレームの描画 (背景・タイトル・棒人間・字幕・進行バー) |
| `make_video.py` | パイプライン本体 (設定値は先頭の定数) |

解像度・fps・尺・間の取り方は `make_video.py` 冒頭と `renderer.py` の `W, H` で変更できます。

## ナレーション音声

上から順に試して、使えたものを採用します。

1. **VOICEVOX ENGINE** — `docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest`
   を起動しておくと自動で使われます (`VOICEVOX_URL` / `VOICEVOX_SPEAKER` で変更可)。
   **VOICEVOXで生成した音声を公開する場合は、各キャラクターの利用規約に沿ったクレジット表記が必要です**
   (例: `VOICEVOX:ずんだもん`)。
2. **OS標準の日本語TTS** — macOS `say -v Kyoko` / Windows SAPI / Linux `open_jtalk`
   (`apt-get install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001`)
3. **音声なし** — 字幕だけで成立するようにタイミングを文字数比で割り当てます

話速はナレーション合計が30秒に収まるよう自動調整されます。

## BGM

リポジトリのルート直下に royalty-free の音声ファイル (`*.mp3` / `*.wav` など、ファイル名に `bgm` を
含むものを優先) を置くと、小音量 (10%) でミックスされます。無ければスキップします。
