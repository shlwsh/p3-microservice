# 配置示例（复制到其他项目后重命名或合并为 config.md）

```markdown
| 变量 | 值 | 说明 |
|------|-----|------|
| PAPER1_ROOT | `path/to/your/paper` | LaTeX 根目录（含 latex/ 或等同结构） |
| 主稿英文 | `{PAPER1_ROOT}/latex/main.tex` | 若无 main.tex，改为实际主文件 |
| 评审输出 | `{PAPER1_ROOT}/reviews/{run_id}/` | 自动创建 |
| 目标期刊 | Nature Communications | 按目标改篇幅标准 |
```

## 目录结构期望

技能默认假设 IMRaD LaTeX 结构：

- `{PAPER1_ROOT}/latex/main.tex` + `latex/sections/*.tex`  
- 可选：`experiments/results/*.json`、`references.bib`、`submission/`  

若结构不同，在 Phase 0 的 `00-上下文清单.md` 中**显式列出**实际主文件与章节目录。

## 可选：弱化 Paper I 专用预检

非 Paper I 项目可删除或忽略 [已知问题清单.md](已知问题清单.md) 中的 C1–C5，在 Phase 1 改为用户提供的预检表。
