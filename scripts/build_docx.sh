#!/usr/bin/env bash
# ============================================================================
# build_docx.sh — 将 latex/main-jos.tex 转换为高质量 DOCX
#
# 转换流水线：
#   1. Python 预处理器：展开 \input、替换自定义命令、PDF→PNG 图片转换
#   2. Pandoc + Lua 过滤器 + 参考模板：生成格式化 DOCX
#   3. 版本化输出到 docs/ 目录
#
# 用法：
#   ./scripts/build_docx.sh [版本号]
#   版本号可选，默认自动递增
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="${ROOT}/scripts"
LATEX_DIR="${ROOT}/latex"
FIGURES_DIR="${ROOT}/figures"
FILTERS_DIR="${SCRIPTS}/pandoc_filters"

# ── 依赖检查 ──────────────────────────────────────────────────────────────
check_deps() {
    local missing=()

    if ! command -v pandoc &>/dev/null; then
        missing+=("pandoc (apt install pandoc)")
    fi

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi

    if ! command -v pdftoppm &>/dev/null; then
        missing+=("pdftoppm (apt install poppler-utils)")
    fi

    # Check python-docx (needed for reference template)
    if ! python3 -c "import docx" 2>/dev/null; then
        missing+=("python-docx (pip install python-docx)")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "缺少依赖："
        for dep in "${missing[@]}"; do
            echo "  ✗ $dep"
        done
        exit 1
    fi
}

echo "=== 检查依赖 ==="
check_deps
echo "  ✓ 所有依赖已就绪"

# ── 版本号 ────────────────────────────────────────────────────────────────
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

echo "=== 版本: v${VERSION} @ ${TS} ==="

# ── 确保参考模板存在 ──────────────────────────────────────────────────────
REF_DOCX="${FILTERS_DIR}/jos_reference.docx"
if [[ ! -f "${REF_DOCX}" ]]; then
    echo "=== 生成参考模板 ==="
    python3 "${SCRIPTS}/build_jos_reference_docx.py"
fi
echo "  ✓ 参考模板: ${REF_DOCX}"

# ── 确保 .bbl 文件存在 ───────────────────────────────────────────────────
BBL_FILE="${LATEX_DIR}/main-jos.bbl"
if [[ ! -f "${BBL_FILE}" ]]; then
    echo "  ⚠ 未找到 ${BBL_FILE}，尝试编译生成..."
    if command -v xelatex &>/dev/null; then
        cd "${LATEX_DIR}"
        export TEXINPUTS="${ROOT}/docs/latex-models/software-journal//:${TEXINPUTS:-}"
        xelatex -interaction=nonstopmode main-jos.tex >/dev/null 2>&1 || true
        bibtex main-jos >/dev/null 2>&1 || true
        cd "${ROOT}"
    fi
fi

if [[ -f "${BBL_FILE}" ]]; then
    echo "  ✓ BBL 文件: ${BBL_FILE}"
else
    echo "  ⚠ BBL 文件不存在，参考文献可能不完整"
fi

# ── 预处理 ────────────────────────────────────────────────────────────────
PREPROCESSED="${LATEX_DIR}/main-jos_pandoc.tex"
echo "=== 预处理 LaTeX ==="
python3 "${SCRIPTS}/preprocess_tex_for_docx.py" \
    --input "latex/main-jos.tex" \
    --output "latex/main-jos_pandoc.tex" \
    --figures-dir "figures" \
    --bbl "latex/main-jos.bbl" \
    --root "${ROOT}"

echo "  ✓ 预处理完成: ${PREPROCESSED}"

# ── Pandoc 转换 ───────────────────────────────────────────────────────────
LUA_FILTER="${FILTERS_DIR}/jos_filter.lua"
echo "=== Pandoc 转换 ==="
pandoc "${PREPROCESSED}" \
    -f latex \
    -t docx \
    -o "${DOCX_DST}" \
    --reference-doc="${REF_DOCX}" \
    --lua-filter="${LUA_FILTER}" \
    --number-sections \
    --wrap=none \
    --resource-path="${FIGURES_DIR}:${LATEX_DIR}" \
    2>&1 | head -20 || true

# ── 验证输出 ──────────────────────────────────────────────────────────────
if [[ -f "${DOCX_DST}" ]]; then
    FILE_SIZE=$(stat -c%s "${DOCX_DST}" 2>/dev/null || stat -f%z "${DOCX_DST}")
    echo ""
    echo "=== 转换成功 ==="
    echo "  文件: ${DOCX_DST}"
    echo "  大小: $(numfmt --to=iec ${FILE_SIZE} 2>/dev/null || echo "${FILE_SIZE} bytes")"

    # Quick validation with python-docx
    python3 -c "
from docx import Document
doc = Document('${DOCX_DST}')
paras = len(doc.paragraphs)
tables = len(doc.tables)
imgs = sum(1 for r in doc.inline_shapes)
print(f'  段落数: {paras}')
print(f'  表格数: {tables}')
print(f'  内嵌图片数: {imgs}')
styles = set(p.style.name for p in doc.paragraphs[:30])
print(f'  使用的样式: {styles}')
" 2>/dev/null || true

else
    echo "转换失败！"
    exit 1
fi

# ── 清理中间文件 ──────────────────────────────────────────────────────────
rm -f "${PREPROCESSED}"
echo ""
echo "=== 完成 ==="
