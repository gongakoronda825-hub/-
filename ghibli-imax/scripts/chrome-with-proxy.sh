#!/bin/sh
# Remotion の headless Chrome は HTTPS_PROXY を読まないので、
# プロキシ環境（クラウドのサンドボックス等）ではフラグで渡す。
# CHROME_BIN で使うブラウザを差し替えられる。
BIN="${CHROME_BIN:-$(dirname "$0")/../node_modules/.remotion/chrome-headless-shell/linux64/chrome-headless-shell-linux64/chrome-headless-shell}"
exec "$BIN" --proxy-server="$HTTPS_PROXY" "$@"
