# paper1-study-handbook — 项目学习手册同步技能

从项目的单一事实出口生成/刷新中文学习手册，默认输出到 `docs/study/`。技能遵守 L0/L1/L2 分层：L0 是机器结果，L1 是验证/审核/归档报告，L2 是学习手册叙事层。

## 文件

| 文件 | 用途 |
|------|------|
| `SKILL.md` | Agent 入口和执行流程 |
| `config.md` | 当前项目路径、L0/L1/L2 和刷新命令 |
| `config.example.md` | 移植模板 |
| `reference.md` | 章节模型、事实源、DoD、校验命令 |

## 触发语

- 更新学习手册 / 同步 study 到最新
- 根据最新论文、实验、评审或文献归档刷新学习手册
- 优化学习手册技能，使其通用化

## 数据流

```text
L0: experiments/results/**/*
        ↓ 汇总脚本或人工校验
L1: docs/验证结果_*.md + docs/*评审*.md + data/papers/cited_papers_manifest.json
        ↓ 本技能同步叙事和答辩材料
L2: docs/study/*.md
```

## 移植步骤

1. 复制技能目录到目标项目的 `.agent/skills/` 或 `.cursor/skills/`。
2. 按 `config.example.md` 创建或更新 `config.md`。
3. 确认 `reference.md` 中“当前关键锚点”已经替换为目标项目事实。
4. 让 Agent 执行“更新学习手册到最新”。

## 设计原则

- 不绑定固定论文编号、旧目录或旧实验字段。
- 不在 study 中维护第二套数字。
- 不声称未实测事项已经完成。
- 对版本化 PDF、文献归档、评审结论和剩余风险做显式同步。
