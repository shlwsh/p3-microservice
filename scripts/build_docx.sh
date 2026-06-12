#!/usr/bin/env bash
# 使用 pandoc 将 latex/main-jos.tex 转换为 docx 格式
# 生成 docs/vN-论文稿件-jos-YYYYMMDD-HHMMSS.docx
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 检查是否安装了 pandoc
if ! command -v pandoc &> /dev/null; then
    echo "未安装 pandoc。请先安装，例如：sudo apt-get install pandoc 或者 brew install pandoc"
    exit 1
fi

# 自动检测 docs/ 下已有稿件的最大版本号，默认 +1
if [[ -n "${1:-}" ]]; then
  VERSION="$1"
else
  MAX_V=$(ls -1 "${ROOT}/docs/" 2>/dev/null \
    | grep -oP '^v\K[0-9]+(?=-论文稿件-)' \
    | sort -n | tail -1)
  VERSION=$(( ${MAX_V:-0} + 1 ))
fi
TS="$(date +%Y%m%d-%H%M%S)"

DOCX_DST="${ROOT}/docs/v${VERSION}-论文稿件-jos-${TS}.docx"

echo "开始转换为 DOCX (v${VERSION} @ ${TS})..."
cd "${ROOT}/latex"

# 运行 pandoc 进行转换
pandoc main-jos.tex \
  -o "${DOCX_DST}" \
  --resource-path=.:../figures \
  --citeproc \
  --bibliography=references.bib

cd "${ROOT}"

echo "转换成功："
echo "${DOCX_DST}"
