# paper1-multi-agent-review — 可移植技能包

多角色模拟同行评审（预检 → 盲审 → 交互质询 → PI 综合 → 落盘报告）。**本目录自包含全部文档**，可复制到任意 Cursor 项目开箱即用。

## 目录文件

| 文件 | 用途 |
|------|------|
| **SKILL.md** | Cursor 入口（Agent 必读） |
| **config.md** | 当前项目的 `PAPER1_ROOT` 等路径 |
| **config.example.md** | 移植到新项目时的配置模板 |
| **reference.md** | 输出清单、模板、速查 |
| **设计方案.md** | Phase 0–5 完整细则与 DoD |
| **角色定义手册.md** | 七角色职责与语气 |
| **已知问题清单.md** | 预检种子 C1–N4（Paper I） |
| **论文领域要点.md** | SQ、B0–B3、审稿人阅读范围 |
| **改稿衔接.md** | 审核后改稿阶段概要 |

## 安装到其他项目

```bash
# 在目标项目根目录执行
mkdir -p .cursor/skills
cp -r /path/to/paper1-multi-agent-review .cursor/skills/
```

1. 编辑 `.cursor/skills/paper1-multi-agent-review/config.md`，设置 **PAPER1_ROOT**。  
2. （可选）按项目改写 `已知问题清单.md`、`论文领域要点.md`。  
3. 在 Cursor 中说：**「执行 Paper I 多角色审核」** 或 @ `paper1-multi-agent-review`。

## 触发语

- 执行 Paper I 多角色审核  
- 模拟审稿人审一遍论文  
- 全面评审建议 / 论文审核  

## 产出位置

```
{PAPER1_ROOT}/reviews/{YYYYMMDD-HHmmss}/
├── 00-上下文清单.md … 05-全面评审报告.md
├── 行动清单.md
└── 执行摘要.md
```

## 与 franka_ros2 文档的关系

`docs-zh/paper1/agent-check/` 中的同名设计稿可与本技能**内容同步**；**可移植副本以本目录为准**。
