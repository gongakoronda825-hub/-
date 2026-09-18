#!/usr/bin/env bash
# 手書き風の日本語フォント (SIL Open Font License) を fonts/ に取ってくる。
# 既に napoleon-video/fonts/ZenKurenaido-Regular.ttf がある場合は不要。
set -euo pipefail
cd "$(dirname "$0")/fonts"
fetch() {  # fetch <GoogleFontsの family 指定> <保存名>
  local css url
  css=$(curl -sS -A "Mozilla/5.0" "https://fonts.googleapis.com/css2?family=$1&display=swap")
  url=$(echo "$css" | grep -o 'https://fonts.gstatic.com[^)]*' | head -1)
  curl -sS -L -o "$2" "$url"
  echo "$2 <- $url"
}
fetch "Zen+Kurenaido" ZenKurenaido-Regular.ttf   # 主に使う鉛筆書き風
# 好みで差し替え:
# fetch "Yomogi" Yomogi-Regular.ttf              # よりゆるい手書き
# fetch "Klee+One:wght@600" KleeOne-SemiBold.ttf # 万年筆・教科書体風
