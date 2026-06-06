# 多角色审核 — 项目配置（p3-microservice）

> 移植到其他项目时复制 [config.example.md](config.example.md) 并修改。

## 项目标识

| 项 | 值 |
|----|-----|
| 项目名 | p3-microservice |
| 论文主题 | 网关驱动动态关注清单的分布式定向日志采集 |
| 目标期刊（主） | 《软件学报》（`latex/main-jos.tex`） |
| 目标期刊（备） | 《计算机学报》（`latex/main-zh.tex`） |
| 主稿 Markdown | `docs/v4-论文稿件.md` |

## 期刊模式

| 变量 | 值 | 说明 |
|------|-----|------|
| **TARGET_JOURNAL** | `JOS`（默认）或 `CJC` | 审核时追加 JOS 专检 |
| JOS 投稿指南 | [软件学报投稿要点.md](软件学报投稿要点.md) | 2026 官网要点 |
| JOS 官网 | https://www.jos.org.cn/ | 仅在线投稿 |
| JOS 模板 | `docs/latex-models/software-journal/` | rjthesis |

## 路径（相对仓库根）

| 变量 | 路径 | 说明 |
|------|------|------|
| **PAPER1_ROOT** | `.` | 仓库根目录 |
| **LATEX_MAIN_ZH** | `latex/main-zh.tex` | CJC 风格 ctexart |
| **LATEX_MAIN_JOS** | `latex/main-jos.tex` | 软件学报 rjthesis |
| **LATEX_SECTIONS** | `latex/sections/zh/` | 中文分节 |
| **L0_RESULTS** | `experiments/results/` | phase1/2/3 JSON |
| **L0_PHASE3** | `experiments/results/phase3/phase3_latest.json` | 主实验机器真相 |
| **L1_DOCS** | `docs/验证结果_*.md` | 人类可读验证摘要 |
| **STUDY** | `docs/study/` | L2 学习手册 |
| **REVIEWS_OUT** | `reviews/{YYYYMMDD-HHmmss}/` | 审核产出 |
| **PAPERS_DIR** | `data/papers/`（根目录 `papers/` 符号链接） | 正文引用文献 PDF/快照 |
| **PAPERS_MANIFEST** | `data/papers/cited_papers_manifest.json` | 文献核实门禁清单 |
| **BIB** | `latex/references.bib` | 参考文献 |

## JOS 文献门槛（预检/领域）

| 指标 | 建议阈值 |
|------|----------|
| 中文或国内期刊 bib 条目 | ≥ **8 篇** 或 ≥ **30%** |
| 正文国内同类对比 | `02_related.tex` 至少 **1 段** 或 **1 表** 分项对比 |

## 作者元数据（编辑/预检核对）

| 字段 | 值 |
|------|-----|
| 第一作者/通讯 | 石洪雷 |
| 单位 | 太原理工大学，山西 太原 030024 |
| 邮箱 | shihonglei0042@link.tyut.edu.cn |
| 基金 | **无**（稿中不得保留基金占位） |

## 审核技能文档

| 文件 | 用途 |
|------|------|
| [审核细则.md](审核细则.md) | **各角色勾选清单（优先读）** |
| [软件学报投稿要点.md](软件学报投稿要点.md) | **JOS 官网要求与退稿高发区** |
| [参考文献归档细则.md](参考文献归档细则.md) | **C6 正文引用文献核实与下载** |
| [已知问题清单.md](已知问题清单.md) | 预检 C1–C6 + J1–J7 |
| [论文领域要点.md](论文领域要点.md) | SQ、基线、国内文献方向 |

## 触发语

- 执行 p3 论文多角色审核 / **软件学报投稿前审核**
- @paper1-multi-agent-review
- 模拟审稿人审一遍论文
