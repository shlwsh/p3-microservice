#!/usr/bin/env python3
"""生成二期实测摘要 docs/验证结果_二期.md"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/results/phase2/phase2_latest.json"
OUT = ROOT / "docs/验证结果_二期.md"


def main():
    if not DATA.exists():
        print(f"缺少 {DATA}")
        return
    d = json.loads(DATA.read_text(encoding="utf-8"))
    comp = d["comparison"]
    dr, fr = d["directed_run"], d["full_run"]
    red = comp["reduction_percent"]

    md = f"""# 二期实测验证结果

> 数据源：`experiments/results/phase2/phase2_latest.json`  
> 方法：WSL Docker 集群 JMeter/并发压测 + Center `/api/v1/stats` + `docker stats`

## 1 定向 vs 全量对比（实测）

| 指标 | 定向采集 | 全量采集 | 降低比例 |
|------|---------|---------|---------|
| 日志量 (K条) | {comp['directed']['log_volume_k']} | {comp['full_collect']['log_volume_k']} | {red['log_volume']}% |
| Agent 平均 CPU (%) | {comp['directed']['cpu_percent']} | {comp['full_collect']['cpu_percent']} | {red['cpu']}% |
| 估算带宽 (MB/s) | {comp['directed']['bandwidth_mbps']} | {comp['full_collect']['bandwidth_mbps']} | {red['bandwidth']}% |

## 2 定向模式明细

- Loki 入库增量：{dr['delta_loki_stored']}
- Redis 网关日志增量：{dr['delta_gateway_redis']}
- 关注清单条目：{dr['attention_list_items']}

## 3 全量模式明细

- Loki 入库增量：{fr['delta_loki_stored']}
- Redis 网关日志增量：{fr['delta_gateway_redis']}

## 4 图表

已更新 `figures/fig3_comparison_bars.pdf`、`fig4_ablation_bars.pdf`（对比图为实测，消融仍用首期模型）。
"""
    OUT.write_text(md, encoding="utf-8")
    print(f"[OK] {OUT}")


if __name__ == "__main__":
    main()
