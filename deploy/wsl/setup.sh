#!/usr/bin/env bash
# WSL2 环境检查与一键启动脚本
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_DIR="${PROJECT_ROOT}/deploy/docker"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_wsl() {
  if grep -qi microsoft /proc/version 2>/dev/null; then
    info "检测到 WSL 环境"
  else
    warn "未检测到 WSL，脚本仍可在 Linux 上运行"
  fi
}

check_docker() {
  if ! command -v docker &>/dev/null; then
    error "未找到 docker 命令"
    echo "  请安装 Docker Desktop（启用 WSL2 集成）或在 WSL 内安装 Docker Engine："
    echo "  https://docs.docker.com/desktop/setup/install/windows-install/"
    exit 1
  fi
  if ! docker info &>/dev/null; then
    error "Docker 守护进程未运行，请启动 Docker Desktop 或 systemctl start docker"
    exit 1
  fi
  info "Docker 可用: $(docker --version)"
}

check_compose() {
  if docker compose version &>/dev/null; then
    info "Docker Compose 可用: $(docker compose version --short)"
  else
    error "未找到 docker compose 插件"
    exit 1
  fi
}

check_project_path() {
  if [[ "${PROJECT_ROOT}" == /mnt/* ]]; then
    warn "项目位于 Windows 挂载盘 (${PROJECT_ROOT})"
    warn "建议将代码克隆到 WSL 原生文件系统（如 ~/work/），可显著提升 I/O 与构建速度"
  else
    info "项目位于 WSL 原生文件系统: ${PROJECT_ROOT}"
  fi
}

check_ports() {
  local ports=(80 3000 3100 6379 8080 9090 9091)
  local busy=()
  for p in "${ports[@]}"; do
    if ss -tln 2>/dev/null | grep -q ":${p} " || netstat -tln 2>/dev/null | grep -q ":${p} "; then
      busy+=("${p}")
    fi
  done
  if [[ ${#busy[@]} -gt 0 ]]; then
    warn "以下端口已被占用，可能导致启动失败: ${busy[*]}"
  else
    info "关键端口检查通过"
  fi
}

start_stack() {
  local use_wsl_overlay="${1:-true}"
  cd "${COMPOSE_DIR}"

  local compose_args=(-f docker-compose.yml)
  if [[ "${use_wsl_overlay}" == "true" ]]; then
    compose_args+=(-f docker-compose.wsl.yml)
    info "启用 WSL 资源优化配置"
  fi

  info "构建并启动集群..."
  docker compose "${compose_args[@]}" up -d --build

  info "等待服务就绪（约 20s）..."
  sleep 20

  "${SCRIPT_DIR}/verify.sh"
}

usage() {
  cat <<EOF
用法: $0 [命令]

命令:
  check     仅执行环境检查（默认）
  start     检查环境并启动完整集群（含 WSL 优化）
  start-full 启动完整集群（不启用 WSL 资源限制）
  stop      停止集群
  logs      查看 Center 日志
  verify    运行健康检查

示例:
  $0 start
  $0 stop
EOF
}

cmd="${1:-check}"

case "${cmd}" in
  check)
    check_wsl
    check_docker
    check_compose
    check_project_path
    check_ports
    info "环境检查完成"
    ;;
  start)
    check_wsl
    check_docker
    check_compose
    check_project_path
    check_ports
    start_stack true
    ;;
  start-full)
    check_wsl
    check_docker
    check_compose
    start_stack false
    ;;
  stop)
    cd "${COMPOSE_DIR}"
    docker compose -f docker-compose.yml -f docker-compose.wsl.yml down
    info "集群已停止"
    ;;
  logs)
    cd "${COMPOSE_DIR}"
    docker compose logs -f center
    ;;
  verify)
    "${SCRIPT_DIR}/verify.sh"
    ;;
  *)
    usage
    exit 1
    ;;
esac
