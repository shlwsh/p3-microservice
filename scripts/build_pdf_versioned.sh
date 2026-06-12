#!/usr/bin/env bash
# 版本化编译：生成 docs/vN-论文稿件-{jos,zh}-YYYYMMDD-HHMMSS.pdf
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

echo "编译 v${VERSION} @ ${TS}"

"${ROOT}/scripts/build_pdf_jos.sh"
"${ROOT}/scripts/build_pdf.sh"

echo "同步最新文稿到 submission 目录..."
# 同步源文件（排除编译中间产物和 PDF）
rsync -av --delete \
  --exclude='*.aux' --exclude='*.log' --exclude='*.out' \
  --exclude='*.bbl' --exclude='*.blg' --exclude='*.toc' \
  --exclude='*.pdf' --exclude='*.synctex*' \
  "${ROOT}/latex/main-jos.tex" \
  "${ROOT}/latex/references.bib" \
  "${ROOT}/latex/sections" \
  "${ROOT}/latex/figures" \
  "${ROOT}/submission/" > /dev/null 2>&1 || true

# 用最新编译好的 JOS 版 PDF 覆盖 submission/论文稿件.pdf
cp -f "${ROOT}/latex/main-jos.pdf" "${ROOT}/submission/论文稿件.pdf"
echo "已同步 submission/论文稿件.pdf（$(date -r "${ROOT}/submission/论文稿件.pdf" '+%Y-%m-%d %H:%M:%S')）"

echo "编译投稿信..."
cd "${ROOT}/submission"
xelatex -interaction=nonstopmode cover_letter.tex > /dev/null 2>&1 || true
cd "${ROOT}"

JOS_SRC="${ROOT}/latex/main-jos.pdf"
ZH_SRC="${ROOT}/latex/main-zh.pdf"
COVER_SRC="${ROOT}/submission/cover_letter.pdf"

JOS_DST="${ROOT}/docs/v${VERSION}-论文稿件-jos-${TS}.pdf"
ZH_DST="${ROOT}/docs/v${VERSION}-论文稿件-zh-${TS}.pdf"
COVER_DST="${ROOT}/docs/v${VERSION}-投稿信-${TS}.pdf"
TAR_DST="${ROOT}/docs/v${VERSION}-投稿包-${TS}.tar.gz"

cp -f "${JOS_SRC}" "${JOS_DST}"
cp -f "${ZH_SRC}" "${ZH_DST}"
if [ -f "${COVER_SRC}" ]; then
  cp -f "${COVER_SRC}" "${COVER_DST}"
fi

# 清理 submission 目录下的编译中间产物，保持投稿包干净
rm -f "${ROOT}/submission/"*.aux "${ROOT}/submission/"*.log \
      "${ROOT}/submission/"*.out "${ROOT}/submission/"*.bbl \
      "${ROOT}/submission/"*.blg "${ROOT}/submission/"*.toc \
      "${ROOT}/submission/"*.synctex* 2>/dev/null || true

echo "打包投稿文件..."
tar -czf "${TAR_DST}" -C "${ROOT}" \
  --exclude='submission/__pycache__' \
  submission/

echo "JOS:  ${JOS_DST}"
echo "ZH:   ${ZH_DST}"
echo "信件: ${COVER_DST}"
echo "打包: ${TAR_DST}"
pdfinfo "${JOS_DST}" 2>/dev/null | grep Pages || true
pdfinfo "${ZH_DST}" 2>/dev/null | grep Pages || true
pdfinfo "${COVER_DST}" 2>/dev/null | grep Pages || true
