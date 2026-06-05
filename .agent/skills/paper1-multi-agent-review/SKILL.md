---
name: paper1-multi-agent-review
description: >-
  Simulates multi-role peer review of an academic LaTeX manuscript (default
  Paper I at doctor/paper1): precheck, blind review, cross-examination, PI
  synthesis, writes reports under {PAPER1_ROOT}/reviews/{run_id}/. Self-contained
  skill pack in .cursor/skills/paper1-multi-agent-review/. Use when the user
  asks to review Paper I, run multi-agent paper review, 执行 Paper I 多角色审核,
  论文审核, or simulate peer reviewers.
disable-model-invocation: false
---

# Paper I 多智能体交互式论文审核

**本技能包自包含**：执行前阅读 [config.md](config.md)；细则见 [设计方案.md](设计方案.md)。

## 启动时必读（按序）

1. [config.md](config.md) — 解析 `PAPER1_ROOT` 与输出路径  
2. [已知问题清单.md](已知问题清单.md) — Phase 1 预检 C1–N4  
3. [论文领域要点.md](论文领域要点.md) — 🔍🔬 审稿上下文  
4. [角色定义手册.md](角色定义手册.md) — 扮演语气与职责  

## 使用时机

- **执行 Paper I 多角色审核** / **模拟审稿人** / **全面评审建议**
- 投稿前要 P0/P1/P2 行动清单与落盘报告
- **默认不改 `.tex`**（改稿见 [改稿衔接.md](改稿衔接.md)）

## 路径（来自 config.md）

| 项 | 默认 |
|----|------|
| `PAPER1_ROOT` | `doctor/paper1` |
| 主稿 | `{PAPER1_ROOT}/latex/main.tex` |
| 输出 | `{PAPER1_ROOT}/reviews/{run_id}/` |
| `run_id` | `YYYYMMDD-HHmmss` |

用户指定其他论文目录时，覆盖 `PAPER1_ROOT`。

## 执行承诺

1. 完成 Phase 0→5，落盘 **12 个文件**（见 [reference.md](reference.md)）  
2. 盲审互不可见；Phase 3 后再交叉引用  
3. Major 问题含 `tex` 路径或 `experiments/results/*` 证据  
4. 数值以仓库 JSON/CSV 为准，禁止编造  
5. 对话末尾贴 [执行摘要](reference.md) 模板内容 + 主报告路径  
6. 中文撰写（引文可英文）

## 任务清单

```text
Phase 0  🎯 → 00-上下文清单.md
Phase 1  📚 → 01-预检报告.md        （对照 已知问题清单.md）
Phase 2  🔍 → 02-审稿人A-方法论.md  （读 论文领域要点.md）
Phase 2  🔬 → 02-审稿人B-领域.md
Phase 2  📊 → 02-统计审查.md
Phase 2  ✍️ → 02-编辑审查.md
Phase 2  📐 → 02-伦理审查.md
Phase 3      → 03-交互质询纪要.md
Phase 4  🎓 → 04-PI综合裁决.md + 行动清单.md
Phase 5  🎯 → 05-全面评审报告.md + 执行摘要.md
```

## 分阶段要点

**Phase 0**：读 `main.tex` 列 `\input`；统计 `sections/*.tex` 行数；列 `experiments/results/*.json`；写 `00-上下文清单.md`。

**Phase 1**：验证 C1–C5（Grep/Read）；输出 `确认的问题` / `待作者确认` / `预检通过项`。

**Phase 2**：五角色顺序输出；Issue 前缀 `METHOD-` `DOMAIN-` `STAT-` `EDIT-` `ETHICS-`；每份含决定、评分、Major/Minor、优点、提问。

**Phase 3**：Top-3 分歧；对话体 🔍→🔬→📊→📚；`[共识]` / `[未共识，交 PI 裁决]`。

**Phase 4**：PI 决定 + P0/P1/P2 `行动清单.md`。

**Phase 5**：合并 [设计方案.md §5.7](设计方案.md) 目录结构 → `05-全面评审报告.md`。

## DoD

- [ ] `{PAPER1_ROOT}/reviews/{run_id}/` 下 12 文件齐全  
- [ ] `05` 含综合问题清单，P0≤7  
- [ ] ≥80% Major 有证据；已核对 `table_ii.json` vs Abstract  
- [ ] C1–C5 均有验证状态  
- [ ] 对话已交付执行摘要  

## 快捷命令

```bash
# 先读 config.md 确认 PAPER1_ROOT
PAPER1_ROOT=doctor/paper1
ls "$PAPER1_ROOT/experiments/results/"*.json
grep -c '\\paragraph' "$PAPER1_ROOT/latex/sections/05_5_discussion.tex"
grep -Ei 'faq|reviewer faq' "$PAPER1_ROOT/latex/sections/" 2>/dev/null || true
grep -c '\\input{sections/05' "$PAPER1_ROOT/latex/main.tex"
```

## 技能包文档索引

| 文件 | 用途 |
|------|------|
| [README.md](README.md) | 复制到其他项目 |
| [设计方案.md](设计方案.md) | 完整 Phase 细则 |
| [reference.md](reference.md) | 模板速查 |
| [改稿衔接.md](改稿衔接.md) | 审核后改稿 |
