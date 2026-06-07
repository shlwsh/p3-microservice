# 学习手册 — 通用章节与校验速查

## 章节模型

| 文件 | 职责 | 数字密度 | 必查项 |
|------|------|----------|--------|
| `README.md` | 阅读顺序、电梯演讲、资源入口 | 低 | 更新日期、投稿状态、最新版本 |
| `01_论文全景与定位.md` | 题目、目标期刊、SQ、贡献、边界、审稿状态 | 中 | 最新审核结论与剩余风险 |
| `02_核心概念与技术原理.md` | 术语、机制、核心 trade-off | 中 | 与最新稿件术语一致 |
| `03_实验数据与图表解读.md` | 主表、图表、阶段、效度威胁 | 高 | 文首 L0/L1 声明；数字可追溯 |
| `04_系统架构与代码地图.md` | 模块、入口、脚本、部署、构建 | 低 | 路径存在；不写过时代码入口 |
| `05_导师拷问速答.md` | 必背数字、审稿问答、陷阱 | 高 | 主结论、条件限制、答辩红线 |
| `06_关键算法详解.md` | 算法、复杂度、实现文件、边界条件 | 中 | 算法与代码/LaTeX 一致 |
| 其它章节 | 项目自定义扩展 | 视情况 | 只在受影响时同步 |

## 事实源优先级

| 类型 | 优先级 | 示例 |
|------|--------|------|
| 机器结果 | L0 | `experiments/results/**/phase*_latest.json` |
| 人类验证报告 | L1 | `docs/验证结果_*.md` |
| 审核/改稿报告 | L1 | `docs/YYYYMMDD-HHMMSS-*评审*.md`、`reviews/*/执行摘要.md` |
| 文献归档 | L1 | `data/papers/cited_papers_manifest.json` |
| 文稿版本 | L1 | `docs/v*-论文稿件-*.pdf`、`latex/references.bib` |
| 学习手册 | L2 | `docs/study/*.md` |

冲突处理：L0 数字优先；L1 解释优先；L2 只叙事，不创建第二套事实源。

## p3 当前关键锚点

用于本仓库 `p3-microservice`；移植到别的项目时替换本节。

| 锚点 | 当前值 | 来源 |
|------|--------|------|
| 主实验 | 8 节点，180 s，并发 50，定向/全量各 3 轮 | `docs/验证结果_三期.md` |
| Loki 入库 | 72±0 vs 4388±1，降低 98.4% | `experiments/results/phase3/phase3_latest.json` |
| Agent CPU | 0.05±0.01% vs 0.08±0.02%，降低 37.5% | 同上 |
| Agent 内存 | 95.6±4.2 MB vs 97.5±1.7 MB，降低 2.0% | 同上 |
| 关注清单 | 16 个 URL 模式 | 同上 |
| 微基准 | 5000 条输入，0.5 ms | `experiments/results/phase1/phase1_latest.json` |
| 最新文稿 | v6 JOS/zh，20260607-090350 | `docs/v6-论文稿件-*.pdf` |
| 正文引用 | 73 篇；中文 30、英文 43 | `docs/20260607-090350-参考文献扩展与归档报告.md` |
| 文献归档 | PDF 21、快照 52、失败 0 | `data/papers/cited_papers_manifest.json` |

## 必须同步的状态

- 投稿目标和处理意见：例如 Major Revision、Minor Revision、投稿前精修。
- 已关闭问题：文献不足、引用归档、编译警告、表格溢出等。
- 剩余风险：实验规模、真实负载、工业基线、实测消融、开源工件等。
- 最新版本化产物：PDF、方案、二评、归档报告。

## 禁止项

- 不复制旧项目固定指标、旧论文名、旧目录作为模板默认值。
- 不在 study 中手工生成第二套实验主表。
- 不把仿真结果写成实测。
- 不声称已完成未实际完成的实验、开源或生产部署。
- 不保留错误的单数论文归档目录别名；本项目统一使用 `data/papers/`。

## 完成定义（DoD）

- [ ] `README.md` 日期、投稿状态、最新版本已更新。
- [ ] `01` 写明最新论文定位、贡献、已关闭问题和剩余风险。
- [ ] `03` 文首含 L0/L1 出处声明，主表数字与 L0/L1 一致。
- [ ] `05` 包含必背数字、审稿高频问答、文献归档状态和实验公平性提醒。
- [ ] 文献统计与 `data/papers/cited_papers_manifest.json` 一致。
- [ ] study 内没有旧模板字段或错误路径。
- [ ] `git diff --check` 通过。

## 校验命令

```bash
# 旧模板字段残留：将 <legacy-pattern> 替换为当前项目已废弃关键词
rg -n '<legacy-pattern>' .agent/skills/paper1-study-handbook docs/study

# 错误归档目录别名残留
find data -maxdepth 1 -type l -name paper -print

# 文献 manifest 摘要
python3 - <<'PY'
import json
from pathlib import Path
p = Path("data/papers/cited_papers_manifest.json")
if p.exists():
    m = json.loads(p.read_text(encoding="utf-8"))
    print(m.get("cited_count"), m.get("summary"))
PY

git diff --check
```
