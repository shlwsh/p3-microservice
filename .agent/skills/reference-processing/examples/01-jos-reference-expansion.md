# 示例：JOS 稿件参考文献扩展到 50+ 并归档

## 场景

用户要求：

- 参考文献不少于 50 篇；
- 文献必须真实存在；
- 中文/英文尽量均衡；
- 中文优先《软件学报》《计算机学报》《计算机研究与发展》；
- 全部引用文献归档到 `data/papers/`；
- 输出报告到 `docs/`；
- 编译文稿保留版本号。

## 操作摘要

1. 统计 `latex/references.bib` 和 `latex/sections/**/*.tex` 中正文唯一 `\cite{}`。
2. 按主题分组检索英文文献：microservice observability、log anomaly detection、AIOps、eBPF、service mesh、RCA。
3. 从 JOS/CJC/CRAD 官网核对中文文献 DOI、卷期页码和 URL。
4. 将筛选文献写入 `latex/references.bib`，并在相关工作节按主题插入正文引用。
5. 运行：

```bash
python3 scripts/verify_cited_papers.py --download
```

6. 修复失败条目：为书籍/官方文档补 URL；错误 DOI 替换为官网可核条目。
7. 输出报告：

```text
docs/YYYYMMDD-HHMMSS-参考文献扩展与归档报告.md
docs/YYYYMMDD-HHMMSS-二次评审报告.md
```

8. 编译并版本化：

```bash
./scripts/build_pdf_jos.sh
./scripts/build_pdf.sh
cp latex/output/main-jos.pdf docs/vN-论文稿件-jos-YYYYMMDD-HHMMSS.pdf
cp latex/output/main-zh.pdf docs/vN-论文稿件-zh-YYYYMMDD-HHMMSS.pdf
```

## 通过口径

以本项目 v6 为例：

| 项 | 结果 |
|----|------|
| 正文唯一引用 | 73 |
| 中文文献 | 30 |
| 英文文献 | 43 |
| PDF 归档 | 21 |
| HTML/CrossRef/官网快照 | 52 |
| paywall/failed | 0 |
| 归档清单 | `data/papers/cited_papers_manifest.json` |

## 常见修复

| 失败 | 修复 |
|------|------|
| 书籍无 DOI/URL | 给 BibTeX 补作者官网、出版社页或 Open Library URL |
| 中文 DOI 不解析 | 用 CHNDOI 或期刊官网核对，不要猜 DOI |
| 出版商页 Cloudflare | CrossRef API 200 即 DOI 有效，归档 CrossRef JSON |
| OpenAlex 返回主题漂移 | 增加 relevance keywords 或换主题查询 |
| 文献数量达标但正文薄弱 | 不用 `\nocite{}`，把引用嵌入相关工作论证 |
