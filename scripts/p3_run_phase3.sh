#!/usr/bin/env bash
# 三期实测：8 节点 + 真实风格日志 + 180s×3 压测
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${ROOT}/deploy/docker"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.wsl.yml -f docker-compose.scale.yml)
cd "${ROOT}"

echo "============================================"
echo " P3 三期实测流水线（8 节点 / 180s / 3 重复）"
echo "============================================"

echo "[1/6] 生成 Agent 配置..."
mkdir -p "${COMPOSE_DIR}/agents"
for i in $(seq 1 8); do
  sed -e "s/agent_id: \"service-agent\"/agent_id: \"service-${i}-agent\"/" \
      -e "s/service_name: \"httpbin\"/service_name: \"service-${i}\"/" \
      "${COMPOSE_DIR}/service-agent-config.yaml" > "${COMPOSE_DIR}/agents/service-${i}-agent.yaml"
done

echo "[2/6] 重建并启动扩展集群（定向模式）..."
cd "${COMPOSE_DIR}"
"${COMPOSE[@]}" up -d --build --force-recreate \
  center gateway gateway-agent \
  service-1 service-2 service-3 service-4 service-5 service-6 service-7 service-8 \
  service-1-agent service-2-agent service-3-agent service-4-agent \
  service-5-agent service-6-agent service-7-agent service-8-agent
sleep 35

echo "[3/6] 定向模式压测（3 重复）..."
python3 - <<'PY'
import json, sys
from pathlib import Path
ROOT = Path("/root/work/p3-microservice")
sys.path.insert(0, str(ROOT / "experiments/scripts"))
import phase3_benchmark as p3

print(f"[phase3] warmup {p3.WARMUP_SEC}s ...")
p3.run_load(p3.WARMUP_SEC)
p3.wait_attention()
directed_runs = [p3.collect_one_run("directed", i) for i in range(p3.REPEATS)]
directed = p3.aggregate_runs(directed_runs)
(ROOT / "experiments/results/phase3").mkdir(parents=True, exist_ok=True)
(ROOT / "experiments/results/phase3/directed_only.json").write_text(
    json.dumps({"directed": directed}, indent=2), encoding="utf-8")
print("directed mean loki:", directed["loki_stored_mean"])
PY

echo "[4/6] 切换全量采集 profile..."
"${COMPOSE[@]}" -f docker-compose.fullcollect.yml -f docker-compose.fullcollect.scale.yml up -d --force-recreate \
  gateway-agent service-1-agent service-2-agent service-3-agent service-4-agent \
  service-5-agent service-6-agent service-7-agent service-8-agent
sleep 20

echo "[5/6] 全量模式压测（3 重复）..."
python3 - <<'PY'
import json, sys
from pathlib import Path
ROOT = Path("/root/work/p3-microservice")
sys.path.insert(0, str(ROOT / "experiments/scripts"))
import phase3_benchmark as p3

full_runs = [p3.collect_one_run("full", i) for i in range(p3.REPEATS)]
full = p3.aggregate_runs(full_runs)
directed = json.loads((ROOT/"experiments/results/phase3/directed_only.json").read_text())["directed"]
comp = p3.build_comparison(directed, full)
payload = {"phase": "phase3", "directed": directed, "full": full, "comparison": comp}
text = json.dumps(payload, ensure_ascii=False, indent=2)
(ROOT/"experiments/results/phase3/phase3_latest.json").write_text(text, encoding="utf-8")
print("comparison:", json.dumps(comp, ensure_ascii=False, indent=2))
PY

echo "[6/6] 恢复定向模式并更新图表..."
"${COMPOSE[@]}" up -d --force-recreate \
  gateway-agent service-1-agent service-2-agent service-3-agent service-4-agent \
  service-5-agent service-6-agent service-7-agent service-8-agent
python3 "${ROOT}/figures/plot_all_phase3.py" || python3 "${ROOT}/figures/plot_all_phase2.py"

echo "完成: experiments/results/phase3/phase3_latest.json"
echo "============================================"
