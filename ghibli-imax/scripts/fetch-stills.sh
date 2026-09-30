#!/bin/sh
# スタジオジブリ公式サイトの場面写真（各作品38枚）を public/stills/ に取得する。
# URL 形式は https://www.ghibli.jp/works/mimi/ ・ /works/karigurashi/ の HTML で確認したもの。
set -e
cd "$(dirname "$0")/.."
mkdir -p public/stills/mimi public/stills/arrietty
for i in $(seq 1 38); do
  n=$(printf %03d "$i")
  curl -sSf -o "public/stills/mimi/mimi$n.jpg" "https://www.ghibli.jp/gallery/mimi$n.jpg"
  curl -sSf -o "public/stills/arrietty/karigurashi$n.jpg" "https://www.ghibli.jp/gallery/karigurashi$n.jpg"
done
