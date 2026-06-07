---
name: paper1-study-handbook
description: >-
  Generates or refreshes a project study handbook under the configured
  STUDY_ROOT (default docs/study) from a single source of truth: L0 machine
  results, L1 human reports, review reports, manuscript versions, and archived
  references. Use when the user asks to update 学习手册, refresh study docs,
  sync study with latest results/reviews/manuscript, or improve the study
  handbook workflow.
disable-model-invocation: false
---

# 学习手册生成与同步

执行前读 [config.md](config.md)；章节、门禁与校验见 [reference.md](reference.md)。本技能应能移植到不同论文/项目，不绑定固定论文编号、实验指标或历史目录。

## 使用时机

- 更新/生成/同步 `docs/study/` 学习手册
- 最新实验、论文版本、参考文献归档、评审报告或投稿状态变化后
- 用户要求“优化学习手册技能”“去除历史模板字段”“让学习手册技能通用化”

## 数据分层

| 层 | 来源 | study 角色 |
|----|------|------------|
| **L0** | `RESULTS_L0` 下 JSON/CSV/日志等机器结果 | 数字真相；冲突时优先 |
| **L1** | `DOCS_L1` 下验证报告、改进方案、二评报告、归档报告 | 人类可读事实摘要 |
| **L2** | `STUDY_ROOT` 下学习手册 | 叙事、答辩、入门、代码地图；不得维护第二套数字 |

## 执行规则

1. 先读 `config.md` 解析项目路径，再读 `reference.md` 决定章节与 DoD。
2. 更新数字时先核对 L0/L1；没有 L0/L1 支撑时，只写“待验证/待补实测”，不编造。
3. 学习手册只链接 L0/L1、论文版本、归档清单和审核报告；避免链接已废弃的第二套结果文档。
4. 投稿/审稿状态来自最新评审或 `docs/` 时间戳报告；保留“已关闭问题”和“剩余风险”。
5. 文献状态来自 `data/papers/cited_papers_manifest.json`，包括 cited 数、PDF/快照数、失败数。
6. 版本化文稿来自 `docs/v*-论文稿件-*.pdf` 或 `config.md` 指定模式；历史版本不得删除。
7. 对现有手册做最小但完整的同步：优先改 README、全景定位、实验数据、导师问答；必要时同步概念、代码地图和算法页。

## 工作流

### Step 0 — 读取现状

- `config.md`：路径、L0/L1/L2、可选刷新命令
- `reference.md`：章节职责、事实源、禁止项、DoD
- `git status --short`：识别已有修改，避免覆盖用户变更
- 最新 L1 报告：验证结果、改进方案、二次评审、参考文献归档报告
- 最新论文版本：`docs/v*-论文稿件-*.pdf`
- 文献 manifest：`data/papers/cited_papers_manifest.json`（若存在）

### Step 1 — 刷新 L1（可选）

若 `config.md` 定义了刷新命令且与当前项目匹配，则运行。若脚本是旧项目模板或与当前仓库不符，跳过并说明原因。

### Step 2 — 更新 L2

| 优先级 | 文件 | 同步内容 |
|--------|------|----------|
| P0 | `README.md` | 更新日期、电梯演讲、投稿状态、最新版本、关联资源 |
| P0 | `01_论文全景与定位.md` | 题目、目标期刊、贡献、边界、最新评审结论 |
| P0 | `03_实验数据与图表解读.md` | L0/L1 声明、主表数字、图表来源、效度威胁 |
| P0 | `05_导师拷问速答.md` | 必背数字、审稿高频问题、剩余风险、文献归档状态 |
| P1 | `02_核心概念与技术原理.md` | 术语、机制、与最新稿件一致的约束/假设 |
| P1 | `04_系统架构与代码地图.md` | 模块路径、构建脚本、版本化文稿/归档路径 |
| P1 | `06_关键算法详解.md` | 算法复杂度、微基准、实现路径、边界条件 |
| P2 | 其它章节 | 仅在存在且受本轮变更影响时更新 |

### Step 3 — 清理历史模板字段

删除或替换不属于当前项目的固定字段，例如旧论文编号、旧目录、旧实验名、旧模型名、旧指标锚点和旧禁止链接。保留通用概念：L0/L1/L2、唯一数字源、版本化产物、归档清单、评审状态。

### Step 4 — 校验

按 `reference.md` 的 DoD 执行。至少检查：

```bash
# 将 <legacy-pattern> 替换为当前项目已废弃的模板关键词或旧路径
rg -n '<legacy-pattern>' .agent/skills/paper1-study-handbook docs/study
find data -maxdepth 1 -type l -name paper -print
git diff --check
```

若当前项目没有这些历史词，命令应无输出；若历史词是项目真实内容，需在最终说明中解释。

### Step 5 — 交付

说明：

- 技能包改了哪些规则文件
- 学习手册改了哪些章节
- 最新数字锚点、版本化 PDF、文献归档统计和剩余风险
- 哪些 L1 刷新命令未运行及原因

## 技能包索引

| 文件 | 用途 |
|------|------|
| [config.md](config.md) | 当前项目路径与刷新命令 |
| [reference.md](reference.md) | 通用章节表、事实源、DoD、校验命令 |
| [config.example.md](config.example.md) | 移植到新项目的配置模板 |
