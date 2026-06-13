<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **p3-microservice** (4751 symbols, 8342 relationships, 169 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/p3-microservice/context` | Codebase overview, check index freshness |
| `gitnexus://repo/p3-microservice/clusters` | All functional areas |
| `gitnexus://repo/p3-microservice/processes` | All execution flows |
| `gitnexus://repo/p3-microservice/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

## Project Agent Skills

技能源目录 `.agent/skills/`；Cursor 通过 `.cursor/skills/` 符号链接自动发现（维护：`bash scripts/link_cursor_skills.sh`）。

| Task | Skill |
|------|-------|
| 文献搜索 / 下载 / 引用核实 | `.cursor/skills/scholar-search/SKILL.md` |
| 参考文献扩展 / 真实文献核验 / 文献归档报告 | `.cursor/skills/reference-processing/SKILL.md` |
| 论文多角色审核 / 投稿前审核 | `.cursor/skills/paper1-multi-agent-review/SKILL.md` |
| 学习手册更新 | `.cursor/skills/paper1-study-handbook/SKILL.md` |
| 智能 Git 提交 | `.cursor/skills/mygit/SKILL.md` |
| 新建技能 | `.cursor/skills/makeskill/SKILL.md` |
| GitNexus MCP 安装 | `.cursor/skills/gitnexus-cursor-mcp-setup/SKILL.md` |
| 中文论文润色 / 去AI味 / 改大白话 | `.cursor/skills/chinese-academic-polish/SKILL.md` |
| 投稿信撰写 / 优化 / 润色 | `.cursor/skills/cover-letter-optimization/SKILL.md` |
| 文档版本化命名 / 投稿附件命名 | `.cursor/skills/doc-naming-convention/SKILL.md` |

匹配上述场景时先读对应 `SKILL.md`；可用 `@技能名` 显式触发。索引见 `.cursor/rules/project-skills.mdc`。
