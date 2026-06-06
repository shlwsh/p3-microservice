# paper1-study-handbook — 学习手册生成技能包

从 **`doctor/paper1` 单一数据出口** 生成/刷新 **`doctor/paper1/docs/study/`** 中文学习手册，避免 `docs-zh/paper1/论文I_*` 与 JSON 数字分叉。

## 目录文件

| 文件 | 用途 |
|------|------|
| **SKILL.md** | Cursor Agent 入口 |
| **config.md** | 本仓库 `PAPER1_ROOT`、`STUDY_ROOT` |
| **config.example.md** | 移植模板 |
| **reference.md** | 章节清单、L0 JSON、DoD、校验命令 |

## 安装到其他项目

```bash
mkdir -p .cursor/skills
cp -r .cursor/skills/paper1-study-handbook /path/to/target/.cursor/skills/
```

1. 编辑 `config.md`（`PAPER1_ROOT`、`STUDY_ROOT`、`SUMMARIZE_SCRIPT`）  
2. 在 Cursor 中说：**「更新学习手册到最新」** 或 @ `paper1-study-handbook`

## 触发语

- 更新学习手册 / 同步 study  
- 生成 Paper I 学习手册  
- @study 刷新到最新实验数字  

## 数据流

```
experiments/results/*.json  (L0)
        ↓ paper1_summarize_full_run.py
doctor/paper1/docs/验证结果_全量.md  (L1)
        ↓ 本技能（叙事 + 答辩）
doctor/paper1/docs/study/*.md  (L2)
```

## 产出位置

- `{STUDY_ROOT}/README.md` + `01`–`08` 章节（默认 `{PAPER1_ROOT}/docs/study`）  
- 不写入 L1 以外的第二套全量数字 Markdown  

## 读者入口

`doctor/paper1/docs/study/README.md`（与 L1 同目录 `doctor/paper1/docs/`）

旧路径 `docs-zh/paper1/study/` 仅 stub 跳转。
