#!/usr/bin/env bash
# 二期实测流水线：重建镜像 → 定向模式压测 → 全量模式压测 → 更新图表与论文数据
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${ROOT}/deploy/docker"
cd "${ROOT}"

echo "============================================"
echo " P3 二期实测流水线"
echo "============================================"

echo "[1/5] 重建并启动集群（定向模式）..."
cd "${COMPOSE_DIR}"
docker compose -f docker-compose.yml -f docker-compose.wsl.yml up -d --build --force-recreate center gateway gateway-agent service-1-agent service-2-agent
sleep 25

echo "[2/5] 定向模式压测..."
COLLECTION_MODE=directed python3 "${ROOT}/experiments/scripts/phase2_benchmark.py" || true

# 仅采集 directed（脚本内会跑两种，此处拆分：先 patch 脚本单模式）
python3 - <<'PY'
import json, subprocess, sys
from pathlib import Path
ROOT = Path("/root/work/p3-microservice")
sys.path.insert(0, str(ROOT / "experiments/scripts"))
import phase2_benchmark as p2

directed = p2.collect_mode_stats("directed")
(ROOT / "experiments/results/phase2").mkdir(parents=True, exist_ok=True)
(ROOT / "experiments/results/phase2/directed_only.json").write_text(json.dumps(directed, indent=2))
print("directed done", directed["delta_loki_stored"])
PY

echo "[3/5] 切换全量采集 profile..."
docker compose -f docker-compose.yml -f docker-compose.wsl.yml -f docker-compose.fullcollect.yml up -d --force-recreate gateway-agent service-1-agent service-2-agent
sleep 15

python3 - <<'PY'
import json, sys
from pathlib import Path
ROOT = Path("/root/work/p3-microservice")
sys.path.insert(0, str(ROOT / "experiments/scripts"))
import phase2_benchmark as p2

full = p2.collect_mode_stats("full")
directed = json.loads((ROOT/"experiments/results/phase2/directed_only.json").read_text())
comp = p2.build_comparison(directed, full)
phase1 = json.loads((ROOT/"experiments/results/phase1/phase1_latest.json").read_text())
payload = {
    "phase": "phase2",
    "directed_run": directed,
    "full_run": full,
    "comparison": comp,
    "ablation": phase1.get("ablation"),
}
text = json.dumps(payload, ensure_ascii=False, indent=2)
out = ROOT / "experiments/results/phase2/phase2_latest.json"
out.write_text(text)
print("comparison:", json.dumps(comp, ensure_ascii=False))
PY

echo "[4/5] 恢复定向模式并生成图表..."
docker compose -f docker-compose.yml -f docker-compose.wsl.yml up -d --force-recreate gateway-agent service-1-agent service-2-agent
python3 "${ROOT}/figures/plot_all_phase2.py"
python3 "${ROOT}/experiments/reports/build_phase2_summary.py"

echo "[5/5] 完成。结果: experiments/results/phase2/phase2_latest.json"
echo "============================================"
