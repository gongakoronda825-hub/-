#!/bin/bash
# 新しいセッションで作業フォルダ(W)を作り直す。使い方: bash ghibli-toolkit/setup.sh <作業フォルダ>
set -e
W=${1:?作業フォルダを指定}; T=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W"/{fonts,models,gb,cut,labsfx,sfx}
cp "$T"/lib/*.py "$W"/
# 各スクリプト冒頭の旧スクラッチパスを作業フォルダに置換
sed -i "s#/tmp/claude-0/-home-user--/e2f1f029-242f-578c-b26c-0ea9dd511990/scratchpad/#$W/#g; s#/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/5a0f7bc1-image.jpg#$T/assets/bg_grid.jpg#g; s#/root/.claude/uploads/e2f1f029-242f-578c-b26c-0ea9dd511990/6a98b9bb-image.jpg#$T/assets/follow.jpg#g" "$W"/*.py
cd "$W/fonts"
FS=https://cdn.jsdelivr.net/npm/@fontsource
for w in 800 900; do
  curl -sSLo jp$w.woff  $FS/m-plus-rounded-1c@5.0.0/files/m-plus-rounded-1c-japanese-$w-normal.woff
  curl -sSLo lat$w.woff $FS/m-plus-rounded-1c@5.0.0/files/m-plus-rounded-1c-latin-$w-normal.woff
done
curl -sSLo mochiy-japanese.woff $FS/mochiy-pop-one@5.0.0/files/mochiy-pop-one-japanese-400-normal.woff
curl -sSLo dela-gothic-one.woff $FS/dela-gothic-one@5.0.0/files/dela-gothic-one-japanese-400-normal.woff
curl -sSLo reggae-one.woff $FS/reggae-one@5.0.0/files/reggae-one-japanese-400-normal.woff
G=https://raw.githubusercontent.com/google/fonts/main/ofl
for w in Medium Bold Black; do curl -sSLo ZenMaru-$w.ttf $G/zenmarugothic/ZenMaruGothic-$w.ttf; done   # 映画・情緒系の動画用（arrietty-imax）
curl -sSLo ZenOldMincho-Bold.ttf $G/zenoldmincho/ZenOldMincho-Bold.ttf
curl -sSLo ZenOldMincho-Regular.ttf $G/zenoldmincho/ZenOldMincho-Regular.ttf
curl -sSLo "CormorantGaramond-Italic[wght].ttf" "$G/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf"
curl -sSLo GreatVibes-Regular.ttf $G/greatvibes/GreatVibes-Regular.ttf
curl -sSLo NotoSerifJP.ttf "$G/notoserifjp/NotoSerifJP%5Bwght%5D.ttf"
curl -sSLo k.zip https://font.sumomo.ne.jp/fontdata-c2157415/k-font.zip && unzip -qjo k.zip '*.ttf' && mv -f keifont*.ttf keifont.ttf 2>/dev/null || true
cd "$W/models"
curl -sSLo isnetis.onnx https://huggingface.co/skytnt/anime-seg/resolve/main/isnetis.onnx
curl -sSLo isnet_gen.onnx https://huggingface.co/imgly/isnet-general-onnx/resolve/main/onnx/model.onnx
cd "$W/gb"
for f in totoro majo laputa chihiro howl mononoke mimi karigurashi ponyo kokurikozaka porco nausicaa; do
  for i in $(seq -f %03g 1 50); do [ -s $f$i.jpg ] || curl -sSfo $f$i.jpg https://www.ghibli.jp/gallery/$f$i.jpg || true; done
done
echo "完了。効果音ラボの音は再配布不可なので labsfx/ に各自ダウンロード（https://soundeffect-lab.info/）"
