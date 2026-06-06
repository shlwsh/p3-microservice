# 参考文献 PDF / 快照归档

> **符号链接**：仓库根 `papers/` → `data/papers/`  
> **门禁脚本**：`python3 scripts/verify_cited_papers.py --download`  
> **清单**：[`cited_papers_manifest.json`](cited_papers_manifest.json)（正文 `\cite{}` 全部条目）

## 当前状态（正文引用 18 篇）

| 类型 | 数量 | 说明 |
|------|------|------|
| PDF (`ok`) | 4 | arXiv + Unpaywall 开放获取 |
| 快照 (`snapshot`) | 14 | 软件学报 HTML、CrossRef JSON、技术文档 HTML 等 |
| 待人工 (`paywall`) | 0 | — |

运行 `python3 scripts/verify_cited_papers.py --download` 后应为 **exit 0**。

## 目录结构

```
data/papers/
├── cited_papers_manifest.json   # ★ 审核门禁清单
├── papers_index.json            # scholar-search 历史索引
├── *.pdf                        # 开放 PDF
├── web_snapshots/               # HTML / CrossRef JSON 快照
└── pending/                     # 应为空（有则未通过门禁）
```

## PDF 示例（开放获取）

| 文件 | cite key | DOI |
|------|----------|-----|
| `2024_Tingting_wang2024rca.pdf` | `wang2024rca` | 10.48550/arXiv.2408.00803 |
| `2023_Shenglin_zhang2023multimodal.pdf` | `zhang2023multimodal` | 10.48550/arXiv.2302.10512 |
| `2020_Jacopo_soldani2020graphrca.pdf` | `soldani2020graphrca` | 10.1016/j.jss.2019.110432 |
| `2024_Wang_...` | （历史 run，未 cited 可保留） | — |

## 中文期刊快照

软件学报等闭源 PDF 以 **官网摘要页 HTML** 归档，例如：

- `web_snapshots/limingshu2019logmgmt.html`
- `web_snapshots/jiatong2020logdiag.html`

## 复现

```bash
python3 scripts/verify_cited_papers.py --download

# 扩展检索（非 cited 门禁）
python .agent/skills/scholar-search/scripts/download_papers.py \
  --input data/scholar/curated.json --output-dir data/papers
```

## 审核技能

见 [`.agent/skills/paper1-multi-agent-review/参考文献归档细则.md`](../.agent/skills/paper1-multi-agent-review/参考文献归档细则.md)。
