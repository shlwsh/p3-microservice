#!/bin/bash
# run_comparison.sh - 对比实验脚本
# 比较定向采集 vs ELK/Loki 全量采集的性能差异
#
# 用法：./run_comparison.sh [节点数] [并发数] [持续时间(秒)]

set -euo pipefail

NODES=${1:-10}
CONCURRENCY=${2:-100}
DURATION=${3:-300}
OUTPUT_DIR="./data/comparison_$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo " 对比实验"
echo " 节点数: ${NODES}"
echo " 并发数: ${CONCURRENCY}"
echo " 持续时间: ${DURATION}s"
echo " 输出目录: ${OUTPUT_DIR}"
echo "============================================"

mkdir -p "${OUTPUT_DIR}"

# ========================================
# 实验 1：定向模式
# ========================================
echo "[Phase 1] 启动定向采集模式..."
docker compose -f deploy/docker/docker-compose.yml up -d

# 等待服务就绪
echo "等待服务就绪..."
sleep 15

# 采集基线指标
echo "采集基线指标..."
curl -s http://localhost:9090/api/v1/query?query=process_cpu_seconds_total > "${OUTPUT_DIR}/baseline_cpu.json"
curl -s http://localhost:9090/api/v1/query?query=process_resident_memory_bytes > "${OUTPUT_DIR}/baseline_mem.json"

# 施加负载
echo "施加 JMeter 负载 (定向模式)..."
jmeter -n \
  -t experiments/jmeter/load_test.jmx \
  -Jthreads=${CONCURRENCY} \
  -Jduration=${DURATION} \
  -Jrampup=30 \
  -l "${OUTPUT_DIR}/directed_results.jtl" \
  -e -o "${OUTPUT_DIR}/directed_report/"

# 采集实验指标
echo "采集定向模式指标..."
sleep 5
curl -s "http://localhost:9090/api/v1/query_range?query=process_cpu_seconds_total&start=$(date -d '-5 min' +%s)&end=$(date +%s)&step=15" > "${OUTPUT_DIR}/directed_cpu.json"
curl -s "http://localhost:9090/api/v1/query_range?query=process_resident_memory_bytes&start=$(date -d '-5 min' +%s)&end=$(date +%s)&step=15" > "${OUTPUT_DIR}/directed_mem.json"

# 查询 Loki 日志量
curl -s "http://localhost:3100/loki/api/v1/query?query=count_over_time({job=\"directed-log-collector\"}[${DURATION}s])" > "${OUTPUT_DIR}/directed_log_count.json"

# 停止定向模式
echo "停止定向模式..."
docker compose -f deploy/docker/docker-compose.yml down

sleep 10

# ========================================
# 实验 2：全量模式（禁用定向过滤）
# ========================================
echo "[Phase 2] 启动全量采集模式..."
# 使用全量配置（禁用定向过滤）
COMPOSE_PROFILES=fullcollect docker compose -f deploy/docker/docker-compose.yml up -d

sleep 15

# 施加相同负载
echo "施加 JMeter 负载 (全量模式)..."
jmeter -n \
  -t experiments/jmeter/load_test.jmx \
  -Jthreads=${CONCURRENCY} \
  -Jduration=${DURATION} \
  -Jrampup=30 \
  -l "${OUTPUT_DIR}/fullcollect_results.jtl" \
  -e -o "${OUTPUT_DIR}/fullcollect_report/"

echo "采集全量模式指标..."
sleep 5
curl -s "http://localhost:9090/api/v1/query_range?query=process_cpu_seconds_total&start=$(date -d '-5 min' +%s)&end=$(date +%s)&step=15" > "${OUTPUT_DIR}/fullcollect_cpu.json"
curl -s "http://localhost:9090/api/v1/query_range?query=process_resident_memory_bytes&start=$(date -d '-5 min' +%s)&end=$(date +%s)&step=15" > "${OUTPUT_DIR}/fullcollect_mem.json"

curl -s "http://localhost:3100/loki/api/v1/query?query=count_over_time({job=\"directed-log-collector\"}[${DURATION}s])" > "${OUTPUT_DIR}/fullcollect_log_count.json"

docker compose -f deploy/docker/docker-compose.yml down

# ========================================
# 生成对比报告
# ========================================
echo "[Phase 3] 生成对比报告..."
python3 experiments/analysis/plot_results.py \
  --directed-dir "${OUTPUT_DIR}" \
  --output-dir "${OUTPUT_DIR}/charts"

echo "============================================"
echo " 实验完成"
echo " 结果目录: ${OUTPUT_DIR}"
echo "============================================"
