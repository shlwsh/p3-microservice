---
name: reference-processing
description: >-
  文献处理与参考文献门禁技能。当用户要求扩充参考文献、保证文献真实存在、下载/归档 cited 文献、平衡中文英文引用、
  修复 references.bib、生成文献处理报告、或执行投稿前 C6 文献核验时使用。该技能编排 scholar-search、
  latex/references.bib、正文 \cite{}、scripts/verify_cited_papers.py 和 data/papers/ 归档流程。
---

# Goal

把“文献不足/引用不可核/未归档”问题处理成可投稿的闭环：真实文献、正文已引用、BibTeX 可编译、`data/papers/` 已归档、`docs/` 有报告。

## Instructions

### 1. 适用边界

使用本技能处理流程和门禁；具体检索、下载脚本参数可继续读取并复用 `../scholar-search/SKILL.md`。

| 场景 | 本技能职责 |
|------|------------|
| 文献不足 | 制定扩展目标、主题分组、中文英文比例、写入正文 |
| 真假核验 | DOI/URL 验证、失败条目替换、禁止记忆 DOI |
| 投稿门禁 | 运行 `verify_cited_papers.py --download`，确认 manifest 通过 |
| 文稿联动 | 必要时重编 PDF、输出时间戳报告、保留历史版本 |

### 2. 基本原则

1. **只统计正文真实引用**：优先修改正文 `\cite{}`；不要用 `\nocite{}` 堆数量。
2. **发现与门禁分离**：`scholar_search.py`/`download_papers.py` 是调研；`verify_cited_papers.py --download` 才是 cited 门禁。
3. **每条 cited 均须可核实**：DOI 走 CrossRef/CHNDOI，URL 走官网可访问；失败就修正或替换。
4. **归档目录唯一**：本项目统一使用 `data/papers/`；不要创建或引用单数形式归档目录别名。
5. **中文文献优先官方源**：《软件学报》《计算机学报》《计算机研究与发展》优先从期刊官网、CHNDOI、官方 PDF/HTML 核对。
6. **英文文献优先可信源**：ACM/IEEE/Elsevier/Springer/Wiley/AAAI/EMSE/JSS/arXiv/OpenTelemetry/Loki/SRE/AWS 等；警惕低质或主题漂移条目。
7. **报告落盘**：过程性方案、归档报告、二次评审报告输出到 `docs/YYYYMMDD-HHMMSS-*.md`。
8. **编译版本化**：若改动 LaTeX 正文或 BibTeX，成功编译后复制为 `docs/v{N}-论文稿件-*-{timestamp}.pdf`，不删除历史版本。

### 3. 输入盘点

先读取：

- `latex/references.bib`
- `latex/sections/**/*.tex`
- 最新 `docs/*评审*.md`、`docs/*参考文献*.md`、`docs/*改进方案*.md`
- `data/papers/cited_papers_manifest.json`（若存在）
- 目标期刊要求；JOS 场景默认关注中文核心文献与国内对比

统计当前状态：

```bash
python3 - <<'PY'
import re, pathlib
bib = pathlib.Path('latex/references.bib').read_text(encoding='utf-8', errors='ignore')
entries = re.findall(r'@\w+\{([^,]+),', bib)
tex = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in pathlib.Path('latex/sections').rglob('*.tex'))
keys = []
for block in re.findall(r'\\cite\{([^}]+)\}', tex):
    keys += [k.strip() for k in block.split(',') if k.strip()]
missing = sorted(set(keys) - set(entries))
unused = [k for k in entries if k not in set(keys)]
print({'bib_entries': len(entries), 'unique_cited': len(set(keys)), 'missing_in_bib': missing, 'unused_bib': len(unused)})
PY
```

### 4. 检索与筛选

英文检索建议分主题，不要一次宽泛搜索：

```bash
.venv-scholar/bin/python .agent/skills/scholar-search/scripts/scholar_search.py \
  --query "microservice observability log collection sampling" \
  --backend openalex --year-from 2020 --num 20 \
  --relevance-keywords "microservice" "log" "observability" "tracing" "AIOps" "sidecar" \
  --output /tmp/refs_obs.json --bibtex /tmp/refs_obs.bib
```

中文检索优先官网或精确网页搜索：

| 期刊 | DOI 前缀 | 核验入口 |
|------|----------|----------|
| 软件学报 | `10.13328/j.cnki.jos.` | `jos.org.cn`、CHNDOI |
| 计算机学报 | `10.11897/SP.J.1016.` | `cjc.ict.ac.cn`、CHNDOI |
| 计算机研究与发展 | `10.7544/issn1000-1239.` | `crad.ict.ac.cn` |

筛选时优先：

- 综述/系统性映射/高引用论文
- 近 5 年前沿，兼顾少量经典基础文献
- 与正文论证点直接相关的文献
- JOS 场景中文文献尽量覆盖软件学报、计算机学报、计算机研究与发展

### 5. 写入 BibTeX 与正文

BibTeX 规则：

- cite key 使用 ASCII、小写、年份，如 `jiatong2020logdiag`、`usman2022observability`
- 中文 DOI 不确定时先核验，不要猜 DOI
- 书籍、官方文档必须有 `url`
- arXiv 条目标明 `journal = {arXiv preprint ...}` 或合适类型

正文规则：

- 在相关工作中按主题成组引用，避免一个段落堆几十篇
- 每组引用必须服务于一句明确论断
- 表格和正文都可引用，但不要只在表中堆数量
- 扩展文献后重新统计唯一正文引用、中文/英文比例

### 6. C6 核验与归档

必跑：

```bash
python3 scripts/verify_cited_papers.py --download
```

通过标准：

| 项 | 要求 |
|----|------|
| `missing_in_bib` | 0 |
| `archive_status` | 全部为 `ok` 或 `snapshot` |
| `paywall` | 0 |
| `failed` | 0 |
| manifest | `data/papers/cited_papers_manifest.json` 与正文 cited 数一致 |

若网络受限或 DOI 请求失败，按系统权限规则用同一命令申请网络权限后重跑。若仍失败，只修对应条目的 DOI/URL 或替换文献。

### 7. 报告与编译

输出报告到 `docs/`，文件名带时间戳：

- `YYYYMMDD-HHMMSS-参考文献扩展与归档报告.md`
- 必要时 `YYYYMMDD-HHMMSS-二次评审报告.md`

报告至少包含：

- 扩展前后正文 cited 数
- 中文/英文数量与占比
- 重点新增中文核心期刊文献
- manifest 汇总：PDF、快照、paywall、failed、doi_valid
- 修改位置：BibTeX、正文节、版本化 PDF
- 剩余风险：篇幅、比例、未完成实验/基线等

若修改 LaTeX：

```bash
./scripts/build_pdf_jos.sh
./scripts/build_pdf.sh
```

随后检查：

```bash
rg -n -F "Overfull \\hbox" latex/output/main-jos.log latex/output/main-zh.log
rg -n "Undefined control sequence|LaTeX Warning: Citation|undefined references|undefined citations|There were undefined|Warning--" latex/output/*.log latex/output/*.blg
git diff --check
```

### 8. 最终交付

向用户报告：

- 新增/更新的文献处理产物
- 正文 cited 数、中文/英文数量
- `data/papers/` manifest 状态
- PDF 编译与日志检查结果
- 未完成事项或需要人工判断的风险

## Examples

见 [examples/01-jos-reference-expansion.md](examples/01-jos-reference-expansion.md)。

## Constraints

- 不保留无法核实 DOI/URL 的正文引用。
- 不把扩展阅读 PDF 当作正文 cited 门禁。
- 不创建单数形式的论文归档目录别名；只使用 `data/papers/`。
- 不删除历史 PDF、历史报告或用户已有文献归档。
- 不声称无法直接下载 PDF 的闭源文献已有 PDF；可说明已保存 CrossRef/官网快照。
- 不为凑数量加入与正文论证无关的引用。
