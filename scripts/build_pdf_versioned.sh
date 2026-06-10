#!/usr/bin/env bash
# 版本化编译：生成 docs/vN-论文稿件-{jos,zh}-YYYYMMDD-HHMMSS.pdf
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-10}"
TS="$(date +%Y%m%d-%H%M%S)"

echo "编译 v${VERSION} @ ${TS}"

"${ROOT}/scripts/build_pdf_jos.sh"
"${ROOT}/scripts/build_pdf.sh"

JOS_SRC="${ROOT}/latex/output/main-jos.pdf"
ZH_SRC="${ROOT}/latex/output/main-zh.pdf"
JOS_DST="${ROOT}/docs/v${VERSION}-论文稿件-jos-${TS}.pdf"
ZH_DST="${ROOT}/docs/v${VERSION}-论文稿件-zh-${TS}.pdf"

cp -f "${JOS_SRC}" "${JOS_DST}"
cp -f "${ZH_SRC}" "${ZH_DST}"

echo "JOS: ${JOS_DST}"
echo "ZH:  ${ZH_DST}"
pdfinfo "${JOS_DST}" 2>/dev/null | grep Pages || true
pdfinfo "${ZH_DST}" 2>/dev/null | grep Pages || true
