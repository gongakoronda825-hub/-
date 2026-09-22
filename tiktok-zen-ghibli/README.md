# 「禅とジブリ」京都展 ナレーション音声

TikTok用の日本語ナレーション音声と、その生成スクリプト。

## 成果物

| ファイル | 形式 | 長さ |
| --- | --- | --- |
| `zen-ghibli-narration.mp3` | MP3 192kbps / 44.1kHz / モノラル | 1分5秒 |
| `zen-ghibli-narration.wav` | WAV 16bit / 24kHz / モノラル | 1分5秒 |

ピークは -1.5 dBFS、平均 -16.3 dBFS に整えてあるので、TikTokに載せても音量が
埋もれない。動画編集はしていない、ナレーション音声のみ。

## 声の設定

- エンジン: VOICEVOX CORE 0.16.4（ローカル合成。APIキー不要・課金なし）
- 声: **青山龍星「しっとり」**（style_id 84）― 低めで落ち着いた男性の声
- `speedScale` 0.95（ゆっくりめ・間延びしない程度）
- `pitchScale` -0.02（わずかに低く）
- `intonationScale` 0.95（抑揚を抑え、大げさな演技にしない）
- 文と文の間に 0.3〜0.6 秒の無音を置き、語りのテンポを作っている
- 話速は約 6.8 モーラ/秒。美術館・ドキュメンタリーの語りに近い速さ

「宮﨑駿」はOpen JTalkが「みやざきしゅん」と読むため、ユーザー辞書で
「ミヤザキハヤオ」に修正している（`USER_WORDS`）。

## クレジット表記（必須）

VOICEVOXの音声を使うため、公開時に以下のクレジットが必要。

```
VOICEVOX:青山龍星
```

青山龍星の音声ライブラリは、個人であればクレジット表記で商用・非商用とも
利用できる。**企業が携わる形で利用する場合は事前確認が必要**
（ななはぴ https://v.seventhh.com/contact/ ）。
詳細は https://www.virvoxproject.com/voicevoxの利用規約 を参照。

## 作り直す

```bash
./setup_assets.sh                 # 素材を ./assets に取得（約120MB）
python3 generate_narration.py     # WAV と MP3 を生成
```

`generate_narration.py` の `SCRIPT` が読み上げる文章、その隣の数値が各文の
直後に入れる無音の秒数。声のトーンは同ファイル上部の定数で調整する。

- `vvcore.py` … VOICEVOX CORE の C API を ctypes から叩く薄いラッパー
- `setup_assets.sh` … コア / ONNX Runtime / Open JTalk辞書 / 音声モデルの取得
- `assets/` は容量が大きいためコミットしていない（`.gitignore`）

MP3の書き出しには `ffmpeg` を使う。入っていない場合は
`pip install imageio-ffmpeg` でも動く（WAVだけなら不要）。
