#!/usr/bin/env bash
# 素材の取得から mp4 の書き出しまで。必要: ffmpeg, python3 (edge-tts, numpy, pillow)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/img fonts

# 画像はスタジオジブリ公式の場面写真ページ (https://www.ghibli.jp/works/mimi/) のものだけを使う
for n in 012 015 020 021 024 025 048; do
  [ -f build/img/mimi$n.jpg ] || curl -fsS -o build/img/mimi$n.jpg https://www.ghibli.jp/gallery/mimi$n.jpg
done
# 冒頭の IMAX 版ポスターは手元のファイルを build/img/imax_poster.jpg に置いておく
[ -f build/img/imax_poster.jpg ] || { echo "build/img/imax_poster.jpg がありません" >&2; exit 1; }
for w in Black ExtraBold; do
  [ -f fonts/MPLUSRounded1c-$w.ttf ] || curl -fsSL -o fonts/MPLUSRounded1c-$w.ttf \
    "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/mplusrounded1c/MPLUSRounded1c-$w.ttf"
done

python3 tts.py build   # プロキシ環境では TTS_CA_BUNDLE に CA の PEM を指定
python3 sfx.py build
python3 build.py mimi_imax_tiktok.mp4
