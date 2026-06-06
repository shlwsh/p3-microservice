# 移植到新项目 — 配置模板

复制技能包后，将本文件内容写入 `config.md` 并改写路径。

| 变量 | 示例 | 说明 |
|------|------|------|
| **PAPER1_ROOT** | `thesis/paper1` | 论文算法仓 |
| **STUDY_ROOT** | `{PAPER1_ROOT}/docs/study` | 学习手册输出目录 |
| **DOCS_L1** | `{PAPER1_ROOT}/docs` | 自动生成汇总 Markdown |
| **RESULTS_L0** | `{PAPER1_ROOT}/experiments/results` | table_ii.json 等 |
| **SUMMARIZE_SCRIPT** | `scripts/summarize_results.py` | 刷新 L1 的脚本（无则手维护 L1） |

**禁止**：在 `STUDY_ROOT` 内链接到项目外第二套「验证结果_*.md」，避免数字分叉。
