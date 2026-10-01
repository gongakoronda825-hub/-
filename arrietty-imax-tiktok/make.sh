#!/usr/bin/env bash
# 素材の取得から mp4 の書き出しまで。必要: ffmpeg, python3 (pillow), docker（VOICEVOX エンジン）
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build/img build/sfx fonts

# 画像はスタジオジブリ公式の場面写真ページ (https://www.ghibli.jp/works/karigurashi/) のものだけを使う
for n in 001 012 018 020 021 024 026 033 038 050; do
  [ -f build/img/karigurashi$n.jpg ] || curl -fsS -o build/img/karigurashi$n.jpg https://www.ghibli.jp/gallery/karigurashi$n.jpg
done
# 冒頭の IMAX 版ポスターは手元のファイルを build/img/imax_poster.jpg に置いておく
[ -f build/img/imax_poster.jpg ] || { echo "build/img/imax_poster.jpg がありません" >&2; exit 1; }
# エンドカードの過去動画サムネイルも手元のファイルを置いておく
for f in follow_1 follow_2; do
  [ -f build/img/$f.jpg ] || { echo "build/img/$f.jpg がありません" >&2; exit 1; }
done
for w in Black ExtraBold; do
  [ -f fonts/MPLUSRounded1c-$w.ttf ] || curl -fsSL -o fonts/MPLUSRounded1c-$w.ttf \
    "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/mplusrounded1c/MPLUSRounded1c-$w.ttf"
done

# 効果音: 効果音ラボ（https://soundeffect-lab.info/）の素材。再配布は禁止なのでリポジトリには入れない
for f in anime/shakin1 anime/sceneswitch1 anime/kira1 anime/slide1; do
  n=$(basename $f); c=$(dirname $f)
  [ -f build/sfx/$n.mp3 ] || curl -fsS -A "Mozilla/5.0" -e "https://soundeffect-lab.info/sound/$c/" \
    -o build/sfx/$n.mp3 "https://soundeffect-lab.info/sound/$c/mp3/$n.mp3"
done

# ナレーション: VOICEVOX エンジン（未起動なら docker で立ち上げる）
if ! curl -fs http://localhost:50021/version >/dev/null; then
  docker run -d --rm -p 50021:50021 voicevox/voicevox_engine:cpu-latest >/dev/null
  until curl -fs http://localhost:50021/version >/dev/null; do sleep 2; done
fi
python3 tts.py build
python3 build.py arrietty_imax_tiktok.mp4
