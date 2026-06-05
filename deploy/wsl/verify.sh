#!/usr/bin/env bash
# 集群健康检查脚本（WSL / 本地 Docker Compose）
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ok=0
fail=0

check() {
  local name="$1"
  local url="$2"
  local expect="${3:-200}"

  if code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "${url}" 2>/dev/null); then
    if [[ "${code}" == "${expect}" ]] || [[ "${expect}" == "any" && "${code}" =~ ^[23] ]]; then
      echo -e "  ${GREEN}✓${NC} ${name} (${url}) → HTTP ${code}"
      ((ok++)) || true
      return
    fi
  fi
  echo -e "  ${RED}✗${NC} ${name} (${url}) → 失败"
  ((fail++)) || true
}

echo "============================================"
echo " 集群健康检查"
echo "============================================"

check "Gateway"        "http://localhost/health"
check "Center HTTP"    "http://localhost:8080/api/v1/health" "any"
check "Loki"           "http://localhost:3100/ready"
check "Grafana"        "http://localhost:3000/api/health"
check "Prometheus"     "http://localhost:9090/-/healthy"
if docker exec redis redis-cli ping 2>/dev/null | grep -q PONG; then
  echo -e "  ${GREEN}✓${NC} Redis (localhost:6379) → PONG"
  ((ok++)) || true
else
  echo -e "  ${RED}✗${NC} Redis (localhost:6379) → 失败"
  ((fail++)) || true
fi

echo "--------------------------------------------"
echo " 通过: ${ok}  失败: ${fail}"
echo "============================================"

if [[ ${fail} -gt 0 ]]; then
  echo "部分服务未就绪，可执行: docker compose -f deploy/docker/docker-compose.yml logs"
  exit 1
fi

echo ""
echo "访问地址:"
echo "  Grafana:    http://localhost:3000  (admin / admin)"
echo "  Center API: http://localhost:8080"
echo "  Gateway:    http://localhost/api/service1/get"
echo "  Prometheus: http://localhost:9090"
echo "  Loki:       http://localhost:3100"
