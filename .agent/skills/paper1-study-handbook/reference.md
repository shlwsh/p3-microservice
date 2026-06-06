# 学习手册 — 章节与校验速查

## 章节清单（Paper I 默认 8+1）

| 文件 | 职责 | 数字密度 |
|------|------|----------|
| `README.md` | 阅读顺序、电梯演讲、关联资源 | 低（回链 L1） |
| `01_论文全景与定位.md` | SQ、贡献、结构、投稿状态 | 低 |
| `02_核心概念与技术原理.md` | Edge-IQA、路由、B0–B4、M1–M6 | 中 |
| `03_实验数据与图表解读.md` | 表/图叙事；**文首声明 L0/L1** | 高（须与 JSON 一致） |
| `04_系统架构与代码地图.md` | 双仓、API、JSONL、验收 | 低 |
| `05_导师拷问速答.md` | 必背数字、陷阱、英文一句 | 高 |
| `06_Edge-IQA算法详解与业界对比.md` | 实现、对比、§6 负分离度答辩 | 中 |
| `07_LangGraph与FSM对比深度分析.md` | 路由基准（routing_benchmark.json） | 中 |
| `08_算法扩展详解.md` | B2d/m/u、物理重采、B4 | 中 |

## L0 核心 JSON

| 文件 | 用途 |
|------|------|
| `table_ii.json` | 主矩阵 18 行 |
| `table_ii_bootstrap.json` | B0–B2 M2 CI |
| `recommended_tau.json` | τ_B2、separation_min_clear_max_blur |
| `recommended_tau_b3.json` | τ_B3 |
| `quick_summary.json` | 快速对照 |
| `algo_quick_summary.json` | B2d/m/u |
| `table_ii_nr.json` | NR-IQA 附录 |
| `cross_tcm_fd.json` | M5 Spearman |
| `network_sweep_quick.json` | 网络扰动 quick |
| `routing_benchmark.json` | LangGraph vs FSM |

## 定稿数字锚点（示例，以 L0 为准）

| 键 | 典型字段 |
|----|----------|
| B2 vs B0 | M1 p50 374→208 ms；M2 0.560→0.604 |
| τ_B2 | 0.465 |
| separation | −0.541 |
| B4 M2 | 0.936 |

刷新 L1 后从 `验证结果_全量.md` 复制到 study，勿手算均值。

## 图表编号（英文 main.pdf）

| Fig | 文件 | 主题 |
|-----|------|------|
| 3 | `fig_iqa_hist.pdf` | 标定重叠 |
| 4 | `fig5_rtt_cdf.pdf` | RTT CDF（simulated） |
| 5 | `fig6_valid_rate.pdf` | M2 柱图 |
| 6 | `fig7_pareto_m2_m1.pdf` | Pareto |
| 7 | `fig7_ablation_tau.pdf` | τ 消融 |

## 禁止引用（study 内）

- `docs-zh/paper1/论文I_*.md`（已 stub，仅跳转）
- `docs-zh/paper1/PaperI_*.md`、`论文I_SCI*.md`（规划类，非数字源）
- 第二套手写 Table II（与 JSON 分叉）

## 允许引用

- `{PAPER1_ROOT}/docs/*`
- `{PAPER1_ROOT}/experiments/results/*`
- `{PAPER1_ROOT}/REPRODUCE.md`、`sim/NETEM.md`
- `{PAPER1_ROOT}/reviews/{run_id}/`（投稿状态）
- study 目录内互链

## 完成定义（DoD）

- [ ] 已运行 `paper1_summarize_full_run.py`（或确认 L1 mtime ≥ L0）
- [ ] `03`、`05` 数字与 `table_ii.json` / `验证结果_全量.md` 一致
- [ ] study 内无 `../论文I_` 链接
- [ ] `03` 文首含 L0/L1 出处声明
- [ ] 负分离度表述为 **−0.541**，无「双峰完全分离」
- [ ] M1 标注 **simulated latency model**
- [ ] M6 与主表混比陷阱在 `05` §八 存在
- [ ] `README.md` 更新日期与投稿状态

## 命令

```bash
# 刷新 L1
python3 scripts/paper1_summarize_full_run.py

# 校验 study 是否仍引用旧 docs-zh 验证文档
rg '论文I_全量|论文I_快速|PaperI_改进' doctor/paper1/docs/study/

# 对照 JSON
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("doctor/paper1/experiments/results/table_ii.json")
rows = json.loads(p.read_text())
from collections import defaultdict
import statistics as st
agg = defaultdict(list)
for r in rows:
    agg[r["baseline"]].append(r["m2_valid_rate"])
for b, xs in sorted(agg.items()):
    print(b, round(st.mean(xs), 3))
PY
```
