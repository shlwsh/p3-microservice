#!/usr/bin/env bash
# 更新 docs/latex-models 下期刊 LaTeX 模板
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS="${ROOT}/docs/latex-models"

echo "==> 计算机学报官方模板"
mkdir -p "${MODELS}/cjc-official"
curl -fsSL -o "${MODELS}/cjc-official/LatexTemplet.zip" \
  "http://cjc.ict.ac.cn/wltg/new/submit/LatexTemplet.zip"
rm -rf "${MODELS}/cjc-official/extracted"
unzip -o -q "${MODELS}/cjc-official/LatexTemplet.zip" -d "${MODELS}/cjc-official/extracted"
echo "    ${MODELS}/cjc-official/extracted/"

echo "==> 计算机学报 Overleaf 适配版"
if [[ -d "${MODELS}/cjc-overleaf/.git" ]]; then
  git -C "${MODELS}/cjc-overleaf" pull --ff-only
else
  git clone --depth 1 \
    https://github.com/DaozeTang/CHINESE-JOURNAL-OF-COMPUTERS--Overleaf-Latex-Template.git \
    "${MODELS}/cjc-overleaf"
fi

echo "==> 软件学报社区模板"
if [[ -d "${MODELS}/software-journal/.git" ]]; then
  git -C "${MODELS}/software-journal" pull --ff-only
else
  git clone --depth 1 \
    https://github.com/VansWaston/software-journal-LaTex-Template.git \
    "${MODELS}/software-journal"
fi

echo "✅ 模板更新完成，见 docs/latex-models/README.md"
