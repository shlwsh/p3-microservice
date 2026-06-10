#!/usr/bin/env bash
# 编译《计算机学报》风格中文初稿 PDF
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEX_DIR="${ROOT}/latex"
MAIN="main-zh"

cd "${TEX_DIR}"

if ! command -v xelatex >/dev/null 2>&1; then
  echo "错误: 未找到 xelatex，请安装 TeX Live（含 ctex）"
  exit 1
fi

run_xelatex() {
  xelatex -interaction=nonstopmode "${MAIN}.tex" || true
}

echo "[1/4] xelatex (第 1 遍)..."
run_xelatex | tail -3

echo "[2/4] bibtex..."
if command -v bibtex >/dev/null 2>&1; then
  bibtex "${MAIN}" || true
fi

echo "[3/4] xelatex (第 2 遍)..."
run_xelatex | tail -3

echo "[4/4] xelatex (第 3 遍)..."
run_xelatex | tail -3

PDF="${TEX_DIR}/${MAIN}.pdf"
if [[ -f "${PDF}" ]]; then
  echo "完成: ${PDF}"
  ls -lh "${PDF}"
else
  echo "编译失败，请查看 ${TEX_DIR}/${MAIN}.log"
  exit 1
fi
