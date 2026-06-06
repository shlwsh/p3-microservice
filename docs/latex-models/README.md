# LaTeX 期刊模板库

本目录存放中文学术期刊 LaTeX 模板，供 `latex/` 下各版本稿件引用。

## 已收录模板

| 期刊 | 目录 | 来源 | 推荐场景 |
|------|------|------|---------|
| **《软件学报》** | [`software-journal/`](./software-journal/) | [VansWaston/software-journal-LaTex-Template](https://github.com/VansWaston/software-journal-LaTex-Template) | 已接入 `latex/main-jos.tex` |
| **《计算机学报》官方** | [`cjc-official/extracted/`](./cjc-official/extracted/) | [官方 LatexTemplet.zip](http://cjc.ict.ac.cn/wltg/new/submit/LatexTemplet.zip) | 权威原版，含 `CjC.cls` + 样例 PDF |
| **《计算机学报》Overleaf 版** | [`cjc-overleaf/`](./cjc-overleaf/) | [DaozeTang/CHINESE-JOURNAL-OF-COMPUTERS--Overleaf-Latex-Template](https://github.com/DaozeTang/CHINESE-JOURNAL-OF-COMPUTERS--Overleaf-Latex-Template) | **推荐本地/XeLaTeX 编译**（修复官方 Bug） |

目录结构：

```
docs/latex-models/
├── README.md                 # 本文件
├── software-journal/         # 软件学报 rjthesis.cls
├── cjc-official/
│   ├── LatexTemplet.zip      # 官方原始包（备份）
│   └── extracted/            # 解压后：CjC.cls, CjC_template_tex.tex, …
└── cjc-overleaf/             # 计算机学报 Overleaf 适配版
```

## 本项目论文编译入口

| 目标期刊 | 命令 | 主文件 | 产出 |
|---------|------|--------|------|
| 软件学报 | `./scripts/build_pdf_jos.sh` | `latex/main-jos.tex` | `docs/v4-论文稿件-jos.pdf` |
| 计算机学报（近似） | `./scripts/build_pdf.sh` | `latex/main-zh.tex` | `latex/main-zh.pdf` |
| 计算机学报（官方 CjC） | 见下文 | `docs/latex-models/cjc-overleaf/CjC_template_tex.tex` | 模板样例 PDF |

> **说明**：`main-zh.tex` 使用 `ctexart` 快速近似计算机学报体例（双语摘要）；正式投稿可迁移至 `CjC.cls` 官方/Overleaf 模板。

---

## 《计算机学报》模板

### 官方版（cjc-official）

- **下载**：http://cjc.ict.ac.cn/wltg/new/submit/LatexTemplet.zip
- **核心文件**：`CjC.cls`、`CjC_template_tex.tex`、`CjC_template_tex.pdf`（样例）
- **编译器**：官方样例基于 `CJKutf8`/GBK，WSL 下建议优先用 Overleaf 适配版
- **特点**：含 `captionhack.sty`、`picins.sty`、`mtpro2.sty` 等配套宏包

### Overleaf 适配版（cjc-overleaf，推荐）

- **文档类**：`\documentclass[10.5pt,compsoc]{CjC}`
- **编译器**：**XeLaTeX**（README 明确推荐）
- **额外**：`gbt7714-numerical.bst` 国标参考文献样式
- **样例输出**：目录内 `CJC1.pdf`

本地试编译样例：

```bash
cd docs/latex-models/cjc-overleaf
xelatex -interaction=nonstopmode CjC_template_tex.tex
```

### 迁移到 CjC 正式稿（待做）

将 `latex/sections/zh/*.tex` 嵌入 `CjC_template_tex.tex` 的双栏 `CJK*` 环境即可；页眉需设置：

```latex
\headoddname{\begin{CJK*}{GBK}{song}? 期 \hfill 作者姓名等：论文题目\end{CJK*}}
```

---

## 《软件学报》模板

- **文档类**：`rjthesis`（`rjthesis.cls`）
- **编译器**：XeLaTeX
- **已接入**：`latex/main-jos.tex` + `./scripts/build_pdf_jos.sh`
- **必填**：`\rjtitle`、`\rjauthor`、`\rjinfor`、`\rjhead`、`rjabstract`、`\rjkeywords`

---

## 一键更新全部模板

```bash
./scripts/update_latex_models.sh
```

或分别更新：

```bash
# 计算机学报官方 zip
curl -fsSL -o docs/latex-models/cjc-official/LatexTemplet.zip \
  http://cjc.ict.ac.cn/wltg/new/submit/LatexTemplet.zip

# Overleaf / 软件学报 git 仓库
git -C docs/latex-models/cjc-overleaf pull
git -C docs/latex-models/software-journal pull
```

---

## 参考链接

| 期刊 | 官网 | 模板 |
|------|------|------|
| 计算机学报 | http://cjc.ict.ac.cn/ | [官方 zip](http://cjc.ict.ac.cn/wltg/new/submit/LatexTemplet.zip) · [Overleaf](https://www.overleaf.com/latex/templates/ji-suan-ji-xue-bao-guan-fang-latexmo-ban-xiu-gai-wei-overleafke-yong-ban/mjhxhmnqvvyn) |
| 软件学报 | https://www.jos.org.cn/ | [GitHub 社区版](https://github.com/VansWaston/software-journal-LaTex-Template) |
