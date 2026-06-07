# p3-microservice 学习手册 — 本仓库配置

| 变量 | 值 | 说明 |
|------|-----|------|
| **PROJECT_ROOT** | `.`（仓库根） | 工程 + 实验 + 论文 |
| **STUDY_ROOT** | `docs/study` | 学习手册（L2 叙事层，中文） |
| **DOCS_L1** | `docs` | 实验数字人类可读汇总（L1） |
| **RESULTS_L0** | `experiments/results` | JSON 唯一机器源（L0） |
| **PAPERS_MANIFEST** | `data/papers/cited_papers_manifest.json` | 正文引用文献核验与归档清单 |
| **REVIEWS** | `reviews` | 多智能体审核报告（可选输入） |
| **VERSIONED_PAPER_PATTERN** | `docs/v*-论文稿件-*.pdf` | 版本化文稿 |

## 解析规则

1. 工作区根 = `p3-microservice` 仓库根目录。
2. 路径 = 工作区根 + 上表相对路径。
3. 实验数字以 L0 JSON 为准；L1 由脚本生成或手工维护，study 只链 L1/L0。
4. 文献归档以 `data/papers/cited_papers_manifest.json` 为准；不要创建或引用单数形式的论文归档别名。

## 相对链接（从 `STUDY_ROOT` 出发）

| 目标 | 相对路径 |
|------|----------|
| docs 索引 | `../README.md`（若存在）或链各 v* 文档 |
| 首期汇总 | `../验证结果_首期.md` |
| 二期汇总 | `../验证结果_二期.md` |
| 三期汇总 | `../验证结果_三期.md` |
| 实验方案 | `../v3-实验方案.md` |
| 设计方案 | `../v1-设计方案.md` |
| 实现方案 | `../v2-实现方案.md` |
| 论文初稿 | `../v4-论文稿件.md` |
| 最新 JOS PDF | `../v6-论文稿件-jos-20260607-090350.pdf` |
| 最新中文 PDF | `../v6-论文稿件-zh-20260607-090350.pdf` |
| 参考文献归档报告 | `../20260607-090350-参考文献扩展与归档报告.md` |
| 二次评审报告 | `../20260607-090350-二次评审报告.md` |
| 部署说明 | `../部署说明.md` |
| 审核报告 | `../../reviews/{run_id}/执行摘要.md` |

## L1 刷新命令

```bash
python3 experiments/reports/build_phase1_summary.py   # → docs/验证结果_首期.md
python3 experiments/reports/build_phase2_summary.py   # → docs/验证结果_二期.md
# 三期摘要见 docs/验证结果_三期.md（与 phase3_latest.json 对齐维护）
```

> 本轮只同步学习手册、论文版本和文献归档状态；未新增实验，因此无需刷新 L0/L1 实验报告。
