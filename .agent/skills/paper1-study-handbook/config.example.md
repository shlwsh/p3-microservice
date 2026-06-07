# 移植到新项目 — 配置模板

复制技能包后，将本文件内容写入 `config.md` 并改写路径。

| 变量 | 示例 | 说明 |
|------|------|------|
| **PROJECT_ROOT** | `.` | 项目根目录 |
| **STUDY_ROOT** | `docs/study` | 学习手册输出目录 |
| **DOCS_L1** | `docs` | 验证报告、评审报告、版本化文稿所在目录 |
| **RESULTS_L0** | `experiments/results` | JSON/CSV/日志等机器结果 |
| **PAPERS_MANIFEST** | `data/papers/cited_papers_manifest.json` | 正文引用文献核验与归档清单 |
| **REVIEWS** | `reviews` | 多角色审核报告目录；没有则留空 |
| **L1_REFRESH_COMMANDS** | `python3 experiments/reports/build_summary.py` | 可选；无脚本则写“无” |
| **VERSIONED_PAPER_PATTERN** | `docs/v*-论文稿件-*.pdf` | 版本化文稿匹配模式 |

## 规则

- study 只读 L0/L1，不另写第二套实验数字。
- 归档目录统一使用 `data/papers/`；不要创建单数形式的论文归档别名。
- 若刷新命令属于旧项目模板或当前项目不存在，跳过并在交付说明中说明。
