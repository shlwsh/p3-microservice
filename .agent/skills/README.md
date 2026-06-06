# 项目 Agent 技能

## 目录说明

| 路径 | 作用 |
|------|------|
| **`.agent/skills/<name>/`** | 技能**源目录**（脚本、文档、SKILL.md） |
| **`.cursor/skills/<name>/`** | Cursor **发现入口**（符号链接 → `.agent/skills/`） |
| **`.claude/skills/gitnexus/`** | GitNexus 代码智能技能（`gitnexus analyze` 生成） |

## 是否自动加载？

| 位置 | Cursor 自动发现 | 自动触发 |
|------|-----------------|----------|
| `.agent/skills/`  alone | ❌ | ❌ |
| `.cursor/skills/`（链接后） | ✅ | ✅（依 `description` 匹配；无 `disable-model-invocation: true`） |
| `.claude/skills/gitnexus/` | ✅ | ✅ |

首次克隆或新增技能后执行：

```bash
bash scripts/link_cursor_skills.sh
```

然后**重启 Cursor** 或新开 Agent 会话。

## 技能列表

| 技能 | 说明 |
|------|------|
| [scholar-search](scholar-search/SKILL.md) | 文献搜索、下载、引用核实（C6） |
| [paper1-multi-agent-review](paper1-multi-agent-review/SKILL.md) | p3 论文多角色审核 |
| [paper1-study-handbook](paper1-study-handbook/SKILL.md) | 学习手册生成/刷新 |
| [mygit](mygit/SKILL.md) | AI 智能 Git 提交 |
| [makeskill](makeskill/SKILL.md) | 新建技能脚手架 |
| [gitnexus-cursor-mcp-setup](gitnexus-cursor-mcp-setup/SKILL.md) | GitNexus MCP 安装 |

## 新建技能

1. 用 `makeskill` 或手动在 `.agent/skills/<name>/` 创建 `SKILL.md`
2. `description` 写清 **做什么 + 何时用**（第三人称，含中英文触发词）
3. 勿加 `disable-model-invocation: true`（除非仅 `@` 手动触发）
4. 运行 `bash scripts/link_cursor_skills.sh`

## 与 Rules 区别

- **Skills**（本目录）：完整工作流，Agent 按需读取 SKILL.md
- **Rules**（`.cursor/rules/*.mdc`）：短约束，如 `scholar-cited-checklist.mdc`、`project-skills.mdc`
