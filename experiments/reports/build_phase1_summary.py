#!/usr/bin/env python3
"""从 L0 结果生成 L1 人类可读摘要 docs/验证结果_首期.md"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "results" / "phase1" / "phase1_latest.json"
OUT = ROOT / "docs" / "验证结果_首期.md"


def main():
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    comp = data["comparison"]
    red = comp["reduction_percent"]
    load = data.get("load_test", {})
    bench = data["attention_list_bench"]
    retry = data.get("retry_tests", {})

    md = f"""# 首期科研验证结果

> 自动生成，数据源：`experiments/results/phase1/phase1_latest.json`  
> 时间戳：{data.get('timestamp', 'N/A')}

## 1 集群健康状态

| 组件 | 状态 |
|------|------|
"""
    for name, info in data.get("health", {}).items():
        ok = "✓" if info.get("ok") else "✗"
        md += f"| {name} | {ok} (HTTP {info.get('status', '-')}) |\n"

    md += f"""
## 2 网关压测

| 指标 | 值 |
|------|-----|
| 总请求数 | {load.get('total', 'N/A')} |
| 成功 | {load.get('success', 'N/A')} |
| 失败 | {load.get('error', 'N/A')} |
| P50 延迟 (ms) | {load.get('latency_p50_ms', 'N/A')} |
| P99 延迟 (ms) | {load.get('latency_p99_ms', 'N/A')} |

## 3 定向 vs 全量对比（首期仿真）

| 指标 | 定向采集 | 全量采集 | 降低比例 |
|------|---------|---------|---------|
| 日志量 (K) | {comp['directed']['log_volume_k']} | {comp['full_collect']['log_volume_k']} | {red['log_volume']}% |
| CPU (%) | {comp['directed']['cpu_percent']} | {comp['full_collect']['cpu_percent']} | {red['cpu']}% |
| 内存 (MB) | {comp['directed']['memory_mb']} | {comp['full_collect']['memory_mb']} | {red['memory']}% |
| 带宽 (MB/s) | {comp['directed']['bandwidth_mbps']} | {comp['full_collect']['bandwidth_mbps']} | {red['bandwidth']}% |

> {comp.get('note', '')}

## 4 关注清单算法微基准

| 指标 | 值 |
|------|-----|
| 输入日志条数 | {bench['input_logs']} |
| 高价值日志 | {bench['high_value_logs']} |
| 泛化模式数 | {bench['unique_patterns']} |
| Top-K | {bench['top_k']} |
| 耗时 (ms) | {bench['elapsed_ms']} |

## 5 指数退避单元测试

| 项 | 值 |
|----|-----|
| 通过 | {'是' if retry.get('passed') else '否'} |

## 6 图表索引

| 图号 | 文件 | 说明 |
|------|------|------|
| 图1 | figures/fig1_system_overview.pdf | 系统总体架构 |
| 图2 | figures/fig2_triple_transform.pdf | 三次转换流程 |
| 图3 | figures/fig3_comparison_bars.pdf | 定向 vs 全量对比 |
| 图4 | figures/fig4_ablation_bars.pdf | 消融实验 |
| 图5 | figures/fig5_backoff_distribution.pdf | 退避延迟分布 |
| 图6 | figures/fig6_attention_bench.pdf | 关注清单微基准 |
"""
    OUT.write_text(md, encoding="utf-8")
    print(f"[OK] {OUT}")


if __name__ == "__main__":
    main()
