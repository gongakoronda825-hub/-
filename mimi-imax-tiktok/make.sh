#!/usr/bin/env bash
# 素材の取得から mp4 の書き出しまで。必要: ffmpeg, python3 (edge-tts, numpy, pillow)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/img fonts

# 画像はスタジオジブリ公式の場面写真ページ (https://www.ghibli.jp/works/mimi/) のものだけを使う
for n in 012 020 021 024 025 029 036 048; do
  [ -f build/img/mimi$n.jpg ] || curl -fsS -o build/img/mimi$n.jpg https://www.ghibli.jp/gallery/mimi$n.jpg
done
for w in Black Bold; do
  [ -f fonts/NotoSansCJKjp-$w.otf ] || curl -fsSL -o fonts/NotoSansCJKjp-$w.otf \
    "https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main/Sans/OTF/Japanese/NotoSansCJKjp-$w.otf"
done

python3 tts.py build   # プロキシ環境では TTS_CA_BUNDLE に CA の PEM を指定
python3 sfx.py build
python3 build.py mimi_imax_tiktok.mp4
