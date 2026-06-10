#!/usr/bin/env bash
# 编译《软件学报》rjthesis 排版稿 PDF
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEX_DIR="${ROOT}/latex"
OUT_DIR="${ROOT}/latex/output"
JOS_CLS="${ROOT}/docs/latex-models/software-journal"
MAIN="main-jos"

cd "${TEX_DIR}"
mkdir -p "${OUT_DIR}"

if ! command -v xelatex >/dev/null 2>&1; then
  echo "错误: 未找到 xelatex，请安装 TeX Live（含 ctex、xeCJK）"
  exit 1
fi

if [[ ! -f "${JOS_CLS}/rjthesis.cls" ]]; then
  echo "错误: 未找到软件学报模板 ${JOS_CLS}/rjthesis.cls"
  echo "请执行: git clone https://github.com/VansWaston/software-journal-LaTex-Template.git ${JOS_CLS}"
  exit 1
fi

# IDE/LaTeX Workshop 诊断需在同目录找到类文件
ln -sf "../docs/latex-models/software-journal/rjthesis.cls" "${TEX_DIR}/rjthesis.cls"

export TEXINPUTS="${JOS_CLS}//:${TEXINPUTS:-}"

run_xelatex() {
  xelatex -interaction=nonstopmode -output-directory="${OUT_DIR}" "${MAIN}.tex" || true
}

echo "[1/4] xelatex (第 1 遍)..."
run_xelatex | tail -5

echo "[2/4] bibtex..."
if command -v bibtex >/dev/null 2>&1; then
  cp -f references.bib "${OUT_DIR}/"
  (cd "${OUT_DIR}" && bibtex "${MAIN}") || true
fi

echo "[3/4] xelatex (第 2 遍)..."
run_xelatex | tail -5

echo "[4/4] xelatex (第 3 遍)..."
run_xelatex | tail -5

PDF="${OUT_DIR}/${MAIN}.pdf"
if [[ -f "${PDF}" ]]; then
  cp -f "${PDF}" "${TEX_DIR}/${MAIN}.pdf"
  cp -f "${PDF}" "${ROOT}/docs/v4-论文稿件-jos.pdf"
  echo "完成: ${PDF}"
  echo "副本: ${TEX_DIR}/${MAIN}.pdf"
  echo "文档: ${ROOT}/docs/v4-论文稿件-jos.pdf"
  ls -lh "${PDF}"
else
  echo "编译失败，请查看 ${OUT_DIR}/${MAIN}.log"
  exit 1
fi
