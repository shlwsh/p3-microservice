# 投稿文件包说明

## 文件清单

| 文件 | 说明 |
|------|------|
| `论文稿件.pdf` | 编译后的完整论文 PDF（软件学报模板，19页） |
| `cover_letter.tex` | 投稿信 LaTeX 源码 |
| `cover_letter.pdf` | 投稿信 PDF |
| `main-jos.tex` | 论文主入口文件（软件学报模板） |
| `rjthesis.cls` | 软件学报样式文件 |
| `references.bib` | 参考文献库 |
| `sections/zh/00_abstract.tex` | 摘要（中英文） |
| `sections/zh/01_intro.tex` | 引言 |
| `sections/zh/02_related.tex` | 相关工作 |
| `sections/zh/03_system.tex` | 系统总体设计 |
| `sections/zh/04_algorithms.tex` | 关键算法 |
| `sections/zh/05_implementation.tex` | 系统实现 |
| `sections/zh/06_experiments.tex` | 实验与分析 |
| `sections/zh/07_conclusion.tex` | 结束语 |
| `figures/fig1-fig8` | 论文图片（PDF 矢量格式） |

## 编译方式

```bash
xelatex main-jos.tex
bibtex main-jos
xelatex main-jos.tex
xelatex main-jos.tex
```

需要 TeX Live 2023+ 和 ctex 宏包支持。

## 作者信息

- **石洪雷**（通讯作者），太原理工大学，shihonglei0042@link.tyut.edu.cn
- **赵涓涓**，太原理工大学教授、博士生导师，zh_juanjuan@126.com
