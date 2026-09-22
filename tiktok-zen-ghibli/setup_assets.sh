#!/usr/bin/env bash
# VOICEVOX CORE でナレーションを合成するための素材を ./assets に用意する。
# 必要なもの: curl, git, python3, tar
set -euo pipefail

CORE_VERSION=0.16.4
ORT_VERSION=1.17.3
DIC_VERSION=1.11
VVM_TAG=0.16.4          # コア0.16系が読める vvm_format_version=1 のモデル
VVM_FILE=15.vvm         # 青山龍星ほかを含む音声モデル

cd "$(dirname "$0")"
ASSETS=${1:-assets}
mkdir -p "$ASSETS"
cd "$ASSETS"

echo "==> VOICEVOX CORE (C API) ${CORE_VERSION}"
curl -fsSL -o core.zip \
  "https://github.com/VOICEVOX/voicevox_core/releases/download/${CORE_VERSION}/voicevox_core-linux-x64-${CORE_VERSION}.zip"
python3 -c "import zipfile; zipfile.ZipFile('core.zip').extractall('.')"

echo "==> VOICEVOX ONNX Runtime ${ORT_VERSION}"
curl -fsSL -o ort.tgz \
  "https://github.com/VOICEVOX/onnxruntime-builder/releases/download/voicevox_onnxruntime-${ORT_VERSION}/voicevox_onnxruntime-linux-x64-${ORT_VERSION}.tgz"
tar xzf ort.tgz

echo "==> Open JTalk 辞書 ${DIC_VERSION}"
curl -fsSL -o open_jtalk_dic.tar.gz \
  "https://github.com/r9y9/open_jtalk/releases/download/v1.11.1/open_jtalk_dic_utf_8-${DIC_VERSION}.tar.gz"
tar xzf open_jtalk_dic.tar.gz

echo "==> 音声モデル ${VVM_FILE} (${VVM_TAG})"
if [ ! -d voicevox_vvm ]; then
  git clone --depth 1 --filter=blob:none --no-checkout \
    https://github.com/VOICEVOX/voicevox_vvm.git voicevox_vvm
fi
(
  cd voicevox_vvm
  git fetch --depth 1 origin tag "${VVM_TAG}" >/dev/null 2>&1 || true
  git checkout -q "${VVM_TAG}" -- "vvms/${VVM_FILE}"
  git checkout -q "${VVM_TAG}" -- TERMS.txt || true
)
mkdir -p vvms
cp "voicevox_vvm/vvms/${VVM_FILE}" vvms/
cp voicevox_vvm/TERMS.txt . 2>/dev/null || true

rm -f core.zip ort.tgz open_jtalk_dic.tar.gz
echo "==> 完了: $(pwd)"
