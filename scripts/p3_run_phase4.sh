#!/usr/bin/env bash
# 四期实测：多规模扩展 + 漏报率 + 端到端延迟 + 基线对照
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="${ROOT}/deploy/docker"
cd "${ROOT}"

NODES="${1:-16}"
echo "============================================"
echo " P3 四期实测（目标规模: ${NODES} 节点）"
echo "============================================"

python3 "${ROOT}/experiments/scripts/generate_scale_compose.py" --nodes "${NODES}"

# 生成 agent 配置
mkdir -p "${COMPOSE_DIR}/agents"
for i in $(seq 1 "${NODES}"); do
  sed -e "s/agent_id: \"service-agent\"/agent_id: \"service-${i}-agent\"/" \
      -e "s/service_name: \"httpbin\"/service_name: \"service-${i}\"/" \
      "${COMPOSE_DIR}/service-agent-config.yaml" > "${COMPOSE_DIR}/agents/service-${i}-agent.yaml"
done

COMPOSE_BASE=(docker compose -f docker-compose.yml)
if [[ "${NODES}" -le 8 ]]; then
  COMPOSE=("${COMPOSE_BASE[@]}" -f docker-compose.wsl.yml -f docker-compose.scale.yml)
  NGINX_CONF="../nginx/nginx.conf"
else
  COMPOSE=("${COMPOSE_BASE[@]}" -f "docker-compose.wsl${NODES}.yml" -f "docker-compose.scale${NODES}.yml")
  NGINX_CONF="../nginx/nginx.scale${NODES}.conf"
  # 临时挂载扩展路由
  export GATEWAY_NGINX_CONF="${NGINX_CONF}"
fi

cd "${COMPOSE_DIR}"

echo "[1/4] 重建集群（${NODES} 节点，定向模式）..."
SERVICES=(center gateway gateway-agent)
for i in $(seq 1 "${NODES}"); do
  SERVICES+=("service-${i}" "service-${i}-agent")
done

if [[ "${NODES}" -gt 8 ]]; then
  # 扩展 nginx 路由：覆盖 gateway 卷
  docker compose -f docker-compose.yml -f "docker-compose.wsl${NODES}.yml" -f "docker-compose.scale${NODES}.yml" \
    up -d --build --force-recreate loki redis prometheus grafana center "${SERVICES[@]}" 2>&1 | tail -20
  docker stop gateway gateway-agent 2>/dev/null || true
  docker rm gateway gateway-agent 2>/dev/null || true
  docker run -d --name gateway --network docker_lognet \
    -p 8088:80 \
    -v "${ROOT}/deploy/nginx/${NGINX_CONF##*/}:/usr/local/openresty/nginx/conf/nginx.conf:ro" \
    -v "${ROOT}/deploy/nginx/lua:/usr/local/openresty/nginx/lua:ro" \
    openresty/openresty:1.25.3.1-alpine
  docker run -d --name gateway-agent --network container:gateway \
    -e AGENT_CONFIG_PATH=/etc/agent/agent.yaml \
    -v "${COMPOSE_DIR}/gateway-agent-config.yaml:/etc/agent/agent.yaml:ro" \
    docker-gateway-agent 2>/dev/null || \
  docker compose -f docker-compose.yml build gateway-agent && \
  docker run -d --name gateway-agent --network container:gateway \
    -e AGENT_CONFIG_PATH=/etc/agent/agent.yaml \
    -v "${COMPOSE_DIR}/gateway-agent-config.yaml:/etc/agent/agent.yaml:ro" \
    docker-gateway-agent
else
  "${COMPOSE[@]}" up -d --build --force-recreate "${SERVICES[@]}"
fi

sleep 40

echo "[2/4] 运行 phase4 基准（规模=${NODES}）..."
cd "${ROOT}"
if [[ "${NODES}" -le 16 ]]; then
  SCALE_NODES="8,${NODES}"
else
  SCALE_NODES="${NODES}"
fi
python3 experiments/scripts/phase4_benchmark.py --nodes "${SCALE_NODES}"

echo "[3/4] 更新图表..."
python3 figures/plot_phase4.py 2>/dev/null || true

echo "[4/4] 完成: experiments/results/phase4/phase4_latest.json"
echo "============================================"
