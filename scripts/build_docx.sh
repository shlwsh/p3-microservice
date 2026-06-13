#!/usr/bin/env bash
# ============================================================================
# build_docx.sh — 将 latex/main-jos.tex 转换为《软件学报》格式 DOCX
#
# 新流水线：
#   1. scripts/build_jos_docx.py 直接解析 LaTeX 主稿、章节、图表、参考文献；
#   2. 按 docs/format/jos_2025_docx_format_definitions.json 写 WordprocessingML；
#   3. scripts/verify_jos_docx.py 对 DOCX、PDF 和格式定义做一致性校验；
#   4. 版本化输出 DOCX 和校验报告到 docs/to-docx/。
#
# 用法：
#   ./scripts/build_docx.sh [版本号]
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="${ROOT}/scripts"
FORMAT_JSON="${ROOT}/docs/format/jos_2025_docx_format_definitions.json"
TEX_SRC="${ROOT}/latex/main-jos.tex"
PDF_SRC="${ROOT}/latex/main-jos.pdf"
OUTPUT_DIR="${ROOT}/docs/to-docx"

check_deps() {
    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    if ! command -v pdftotext &>/dev/null; then
        missing+=("pdftotext (apt install poppler-utils)")
    fi
    if ! python3 -c "from PIL import Image" 2>/dev/null; then
        missing+=("Pillow/PIL (用于读取图片尺寸)")
    fi
    if [[ ! -f "${FORMAT_JSON}" ]]; then
        missing+=("${FORMAT_JSON}")
    fi
    if [[ ! -f "${TEX_SRC}" ]]; then
        missing+=("${TEX_SRC}")
    fi
    if [[ ! -f "${PDF_SRC}" ]]; then
        missing+=("${PDF_SRC} (请先运行 scripts/build_pdf_jos.sh)")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "缺少依赖或输入："
        for dep in "${missing[@]}"; do
            echo "  ✗ ${dep}"
        done
        exit 1
    fi
}

echo "=== 检查依赖与输入 ==="
check_deps
echo "  ✓ 依赖与输入已就绪"

mkdir -p "${OUTPUT_DIR}"

if [[ -n "${1:-}" ]]; then
    VERSION="$1"
else
    MAX_V="$(find "${ROOT}/docs" -type f -name 'v*-论文稿件-*' -printf '%f\n' \
        | sed -n 's/^v\([0-9]\+\)-论文稿件-.*/\1/p' \
        | sort -n \
        | tail -1 || true)"
    VERSION=$(( ${MAX_V:-0} + 1 ))
fi

TS="$(date +%Y%m%d-%H%M%S)"
DOCX_DST="${OUTPUT_DIR}/v${VERSION}-论文稿件-jos-${TS}.docx"
REPORT_DST="${OUTPUT_DIR}/v${VERSION}-论文稿件-jos-${TS}-docx校验报告.md"
REPORT_JSON="${OUTPUT_DIR}/v${VERSION}-论文稿件-jos-${TS}-docx校验报告.json"

echo "=== 版本: v${VERSION} @ ${TS} ==="
echo "=== 生成 DOCX ==="
python3 "${SCRIPTS}/build_jos_docx.py" \
    --root "${ROOT}" \
    --format "docs/format/jos_2025_docx_format_definitions.json" \
    --output "${DOCX_DST}"

echo "=== 校验 DOCX 与 PDF/格式定义一致性 ==="
python3 "${SCRIPTS}/verify_jos_docx.py" \
    --docx "${DOCX_DST}" \
    --pdf "${PDF_SRC}" \
    --format "${FORMAT_JSON}" \
    --report "${REPORT_DST}" \
    --json-report "${REPORT_JSON}"

FILE_SIZE=$(stat -c%s "${DOCX_DST}" 2>/dev/null || stat -f%z "${DOCX_DST}")

echo ""
echo "=== 完成 ==="
echo "  DOCX: ${DOCX_DST}"
echo "  校验报告: ${REPORT_DST}"
echo "  大小: $(numfmt --to=iec "${FILE_SIZE}" 2>/dev/null || echo "${FILE_SIZE} bytes")"
