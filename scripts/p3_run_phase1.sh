#!/usr/bin/env bash
# 首期科研工作流：数据采集 → 图表生成 → 验证结果文档
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "============================================"
echo " P3 首期科研流水线"
echo "============================================"

# 1. 可选：确认集群就绪
if [[ "${SKIP_HEALTH:-}" != "1" ]]; then
  if [[ -x deploy/wsl/verify.sh ]]; then
    deploy/wsl/verify.sh || echo "[WARN] 集群未完全就绪，继续采集可用指标"
  fi
fi

# 2. L0 数据采集
echo "[1/3] 采集首期实验数据..."
python3 experiments/scripts/phase1_collect.py

# 3. 图表生成
echo "[2/3] 生成论文图表..."
python3 figures/plot_all_phase1.py

# 4. 生成 L1 摘要
echo "[3/3] 生成验证结果摘要..."
python3 experiments/reports/build_phase1_summary.py

echo "============================================"
echo " 首期科研步骤完成"
echo " 数据: experiments/results/phase1/phase1_latest.json"
echo " 图表: figures/fig1_*.pdf ... fig6_*.pdf"
echo " 摘要: docs/验证结果_首期.md"
echo "============================================"
