#!/usr/bin/env bash
# 编译《软件学报》rjthesis 排版稿 PDF
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEX_DIR="${ROOT}/latex"
JOS_CLS="${ROOT}/docs/latex-models/software-journal"
MAIN="main-jos"

cd "${TEX_DIR}"

if ! command -v xelatex >/dev/null 2>&1; then
  echo "错误: 未找到 xelatex，请安装 TeX Live（含 ctex、xeCJK）"
  exit 1
fi

if [[ ! -f "${JOS_CLS}/rjthesis.cls" ]]; then
  echo "错误: 未找到软件学报模板 ${JOS_CLS}/rjthesis.cls"
  echo "请执行: git clone https://github.com/VansWaston/software-journal-LaTex-Template.git ${JOS_CLS}"
  exit 1
fi

# 

export TEXINPUTS="${JOS_CLS}//:${TEXINPUTS:-}"

run_xelatex() {
  xelatex -interaction=nonstopmode "${MAIN}.tex" || true
}

echo "[1/4] xelatex (第 1 遍)..."
run_xelatex | tail -5

echo "[2/4] bibtex..."
if command -v bibtex >/dev/null 2>&1; then
  bibtex "${MAIN}" || true
fi

echo "[3/4] xelatex (第 2 遍)..."
run_xelatex | tail -5

echo "[4/4] xelatex (第 3 遍)..."
run_xelatex | tail -5

PDF="${TEX_DIR}/${MAIN}.pdf"
if [[ -f "${PDF}" ]]; then
  cp -f "${PDF}" "${ROOT}/docs/v4-论文稿件-jos.pdf"
  echo "完成: ${PDF}"
  echo "文档: ${ROOT}/docs/v4-论文稿件-jos.pdf"
  ls -lh "${PDF}"
else
  echo "编译失败，请查看 ${TEX_DIR}/${MAIN}.log"
  exit 1
fi
