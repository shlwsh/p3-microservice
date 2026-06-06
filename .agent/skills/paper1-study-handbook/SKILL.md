---
name: paper1-study-handbook
description: >-
  Generates or refreshes the Paper I Chinese study handbook under doctor/paper1/docs/study/
  from doctor/paper1 single data outlet (experiments/results JSON + docs/ markdown).
  Enforces L0/L1/L2 layering, removes duplicate number sources, syncs figures and review
  status. Use when the user asks to update 学习手册, generate study handbook, sync study
  with latest results, 更新 study, or @study handbook refresh.
disable-model-invocation: false
---

# Paper I 学习手册生成与同步

**自包含技能包**：执行前读 [config.md](config.md)；细则见 [reference.md](reference.md)。

## 使用时机

- **更新学习手册** / **同步 study 到最新** / **@study 刷新**
- 全量实验、Minor Revision 改稿、或 `table_ii.json` 变更后
- 新学生入门文档需要与投稿数字一致

## 三层数据出口（必须遵守）

| 层 | 路径 | study 角色 |
|----|------|------------|
| **L0** | `{PAPER1_ROOT}/experiments/results/*.json` | 唯一机器源；冲突以 L0 为准 |
| **L1** | `{PAPER1_ROOT}/docs/验证结果_*.md` | 人类可读汇总；study **只链 L1/L0** |
| **L2** | `{STUDY_ROOT}/` | 叙事、答辩、架构；**禁止**链 `docs-zh/paper1/论文I_*` |

## 执行承诺

1. **先刷新 L1**，再改 study 数字章节  
2. 所有实验数字来自 L0 或 L1，**不编造**  
3. 输出**中文**；路径用仓库相对路径或 `` `doctor/paper1/...` ``  
4. **最小 diff**：只改与数据/结构/审核相关的段落  
5. 不新建 `docs-zh/paper1/论文I_*.md` 数字副本  

## 工作流（按序）

### Step 0 — 读配置与现状

1. [config.md](config.md) → 解析 `PAPER1_ROOT`、`STUDY_ROOT`  
2. Read：`{DOCS_L1}/验证结果_全量.md`、`table_ii.json`、`recommended_tau.json`  
3. 若有最新审核：Read `{REVIEWS}/` 下最新 `run_id/执行摘要.md`（可选）  
4. `rg '论文I_|PaperI_改进|docs-zh/paper1/V19' {STUDY_ROOT}/` → 待清理外链  

### Step 1 — 刷新 L1（仓库根目录）

```bash
python3 scripts/paper1_summarize_full_run.py
```

确认生成：`{PAPER1_ROOT}/docs/验证结果_全量.md`。  
改稿产物若缺失：`python3 {PAPER1_ROOT}/experiments/reports/build_paper1_artifacts.py`

### Step 2 — 按章节更新 L2

| 优先级 | 文件 | 动作 |
|--------|------|------|
| P0 | `README.md` | 阅读顺序、电梯演讲、关联资源 → 链 L1（`../验证结果_*.md`） |
| P0 | `03_实验数据与图表解读.md` | 文首 L0/L1 声明；Table/Fig 与 L1 一致；Fig 编号见 reference |
| P0 | `05_导师拷问速答.md` | §一必背数字、§八陷阱、负分离度/仿真 RTT |
| P1 | `01_论文全景与定位.md` | 工程状态、5 实验节、审核结论 |
| P1 | `02_核心概念与技术原理.md` | separation<0；M5 描述性；无「双峰分离」 |
| P1 | `06` §6 | 负分离度答辩四支柱（有则校对，无则补） |
| P2 | `04`、`07`、`08` | 路径、基准 JSON、算法 quick 数字 |

**03 文首模板**（必须有）：

```markdown
> **数字出处（唯一）**：[`验证结果_全量.md`](../验证结果_全量.md) · `doctor/paper1/experiments/results/table_ii.json`
```

**study 内链接规则**：到 L1 用 `../验证结果_*.md`、`../README.md`；到 PAPER1_ROOT 其它文档用 `../../REPRODUCE.md` 等；到 JSON 用 `` `doctor/paper1/experiments/results/...` ``。

### Step 3 — 清理禁止引用

删除或替换为 L1/L0：

- `../论文I_全量验证结果_*.md`
- `../论文I_快速验证结果_*.md`
- `../PaperI_改进方案.md`、`../论文I_科研任务*.md`
- `../TCM-FD_*.md` → 改为 `experiments/configs/tcm_paths.yaml` 或脚本路径

### Step 4 — 校验 DoD

对照 [reference.md](reference.md) DoD 清单；运行：

```bash
rg '论文I_全量|论文I_快速|PaperI_改进|双峰分离|双峰完全' doctor/paper1/docs/study/ || true
```

### Step 5 — 交付

向用户说明：

- 更新了哪些 study 文件  
- L1 是否已重新生成  
- 定稿数字锚点（B2 M1/M2、τ、separation）  
- 剩余 stub：`docs-zh/paper1/论文I_*.md` 仅跳转，勿编辑  

## 与其它技能衔接

| 场景 | 技能 |
|------|------|
| 改稿前先审 | `paper1-multi-agent-review` |
| LaTeX 中英同步 | `paper1-bilingual-translation` |
| 仅复现实验 | 读 `{PAPER1_ROOT}/REPRODUCE.md`，不必改 study |

## 常见陷阱（写入 study 时规避）

| 错误 | 正确 |
|------|------|
| M6 p50 与 B2 M1 比快慢 | M6 测量栈不同，仅趋势 |
| separation > 0 | **−0.541**，Fig.3 重叠 |
| Table II 来自 Franka | 来自 `run_matrix_tcm.py` + 仿真 RTT |
| B3 M2 低于 B2 | 全量 B3 **高于** B2，B2 主 claim 在 RTT/可解释 |

## 技能包索引

| 文件 | 用途 |
|------|------|
| [README.md](README.md) | 移植说明 |
| [config.example.md](config.example.md) | 新项目模板 |
| [reference.md](reference.md) | 章节表、JSON 表、DoD |
