#!/bin/bash
# run_ablation.sh - 消融实验脚本
# 逐一移除关键模块，验证各模块的独立贡献
#
# 消融组：
# A1: 移除动态清单（所有日志均采集）
# A2: 移除固定缓存块（无限缓存 + 同步上传）
# A3: 移除指数退避（固定间隔重试）
# A4: 移除压力感知（忽略系统负载）

set -euo pipefail

CONCURRENCY=${1:-100}
DURATION=${2:-180}
REPEATS=${3:-3}
OUTPUT_DIR="./data/ablation_$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo " 消融实验"
echo " 并发数: ${CONCURRENCY}"
echo " 持续时间: ${DURATION}s"
echo " 重复次数: ${REPEATS}"
echo "============================================"

mkdir -p "${OUTPUT_DIR}"

# 消融实验配置
declare -A ABLATION_CONFIGS
ABLATION_CONFIGS[baseline]="all_enabled"
ABLATION_CONFIGS[no_attention_list]="disable_attention_list"
ABLATION_CONFIGS[no_fixed_cache]="disable_fixed_cache"
ABLATION_CONFIGS[no_backoff]="disable_exponential_backoff"
ABLATION_CONFIGS[no_pressure]="disable_pressure_awareness"

for config_name in baseline no_attention_list no_fixed_cache no_backoff no_pressure; do
    config_desc="${ABLATION_CONFIGS[$config_name]}"
    echo ""
    echo "=========================================="
    echo " 消融组: ${config_name} (${config_desc})"
    echo "=========================================="

    for repeat in $(seq 1 ${REPEATS}); do
        echo "[${config_name}] 第 ${repeat}/${REPEATS} 次实验..."
        run_dir="${OUTPUT_DIR}/${config_name}/run_${repeat}"
        mkdir -p "${run_dir}"

        # 启动对应配置的集群
        ABLATION_CONFIG="${config_name}" \
          docker compose -f deploy/docker/docker-compose.yml up -d
        sleep 15

        # 施加负载
        jmeter -n \
          -t experiment/jmeter/load_test.jmx \
          -Jthreads=${CONCURRENCY} \
          -Jduration=${DURATION} \
          -Jrampup=15 \
          -l "${run_dir}/results.jtl" \
          2>/dev/null

        # 采集指标
        sleep 5
        curl -s http://localhost:9090/api/v1/query?query=process_cpu_seconds_total > "${run_dir}/cpu.json" 2>/dev/null
        curl -s http://localhost:9090/api/v1/query?query=process_resident_memory_bytes > "${run_dir}/mem.json" 2>/dev/null

        # 采集 Agent 特有指标
        curl -s http://localhost:9100/metrics > "${run_dir}/agent_metrics.txt" 2>/dev/null

        # 日志量统计
        curl -s "http://localhost:3100/loki/api/v1/query?query=count_over_time({job=\"directed-log-collector\"}[${DURATION}s])" > "${run_dir}/log_count.json" 2>/dev/null

        docker compose -f deploy/docker/docker-compose.yml down 2>/dev/null
        sleep 5
    done
done

# 汇总分析
echo ""
echo "=========================================="
echo " 生成消融分析报告..."
echo "=========================================="

python3 experiment/analysis/plot_results.py \
  --ablation-dir "${OUTPUT_DIR}" \
  --output-dir "${OUTPUT_DIR}/charts"

echo "消融实验完成，结果目录: ${OUTPUT_DIR}"
