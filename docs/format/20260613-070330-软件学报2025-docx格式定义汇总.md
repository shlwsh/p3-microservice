# 软件学报 2025 年版 Word 样例格式定义提取

源文件：`docs/latex-models/software-journal/软件学报排版样例2025年版.docx`

## 1. 页面设置

| 项 | Word XML 值 | 换算 |
|----|------------|------|
| 纸张 | `{'w': '10433', 'h': '14742'}` | 18.4 cm × 26.0 cm |
| 页边距 | `{'top': '567', 'right': '822', 'bottom': '1247', 'left': '822', 'header': '737', 'footer': '567', 'gutter': '0'}` | {'top': 1.0, 'right': 1.45, 'bottom': 2.199, 'left': 1.45, 'header': 1.3, 'footer': 1.0, 'gutter': 0.0} |
| 分栏 | `{'space': '720', 'num': '1'}` | 单栏 |
| 首页独立页眉页脚 | `True` | Word `titlePg` |

## 2. 页眉页脚文本

### headers
- `word/header1.xml`: 贾修一 等:基于变分自编码器的异构缺陷预测特征表示方法 | 2211
- `word/header2.xml`: 2210 | 软件学报 20XX年第XX卷第XX期

### footers
- `word/footer1.xml`: (empty)
- `word/footer2.xml`: (empty)
- `word/footer3.xml`: (empty)

## 3. 关键样式定义

| styleId | 名称 | 类型 | 对齐 | 字号 pt | 字体 | 段前/段后/行距 | 缩进 |
|---------|------|------|------|---------|------|----------------|------|
| 1 | Normal | paragraph | both | 9.0 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '宋体', 'cs': 'Times New Roman'}` | `{}` | `{}` |
| 91 | Normal Table | table |  |  | `{}` | `{}` | `{}` |
| 22 | Normal Indent | paragraph |  |  | `{}` | `{}` | `{'firstLine': '420', 'firstLineChars': '200'}` |
| 64 | Subtitle | paragraph |  | 18.0 | `{'eastAsia': '黑体'}` | `{'before': '320'}` | `{}` |
| 65 | 作者 | paragraph | left | 14.0 | `{'eastAsia': '仿宋_GB2312'}` | `{'before': '160', 'after': '240', 'line': '0', 'lineRule': 'atLeast'}` | `{}` |
| 66 | 单位 | paragraph | both | 8.5 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '宋体', 'cs': 'Times New Roman'}` | `{}` | `{'left': '70', 'hanging': '70', 'hangingChars': '70'}` |
| 84 | Normal (Web) | paragraph |  | 12.0 | `{}` | `{}` | `{}` |
| 87 | Title | paragraph | center | 16.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'cs': 'Arial'}` | `{'before': '240', 'after': '60'}` | `{}` |
| 101 | 标题 3 Char | character |  | 9.0 | `{}` | `{}` | `{}` |
| 102 | 标题 4 Char | character |  | 9.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'eastAsia': '黑体'}` | `{}` | `{}` |
| 103 | 标题 5 Char | character |  | 14.0 | `{}` | `{}` | `{}` |
| 104 | 标题 6 Char | character |  | 9.0 | `{}` | `{}` | `{}` |
| 105 | 标题 7 Char | character |  | 12.0 | `{}` | `{}` | `{}` |
| 106 | 标题 8 Char | character |  | 12.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'eastAsia': '黑体'}` | `{}` | `{}` |
| 107 | 标题 9 Char | character |  | 9.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'eastAsia': '黑体'}` | `{}` | `{}` |
| 112 | Depart.Correspond.http | paragraph |  | 8.0 | `{}` | `{}` | `{'left': '66', 'hanging': '66', 'hangingChars': '66'}` |
| 113 | Date | paragraph |  | 9.0 | `{}` | `{'after': '240'}` | `{}` |
| 115 | Abstract | paragraph | both | 9.0 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '楷体_GB2312', 'cs': 'Times New Roman'}` | `{}` | `{}` |
| 117 | 摘要 | paragraph |  |  | `{'eastAsia': '楷体_GB2312'}` | `{}` | `{'firstLine': '0', 'firstLineChars': '0'}` |
| 118 | 关键词 | paragraph |  |  | `{}` | `{}` | `{'left': '429', 'hanging': '429', 'hangingChars': '429'}` |
| 120 | Title | paragraph |  | 12.0 | `{'eastAsia': '黑体'}` | `{'before': '240', 'after': '100'}` | `{}` |
| 121 | Name | paragraph | left | 9.0 | `{'ascii': 'Times New Roman', 'eastAsia': '宋体'}` | `{'before': '220', 'after': '180'}` | `{}` |
| 124 | 副标题 Char | character |  | 18.0 | `{'eastAsia': '黑体'}` | `{}` | `{}` |
| 125 | 表名 | paragraph |  |  | `{}` | `{'after': '120'}` | `{}` |
| 126 | Reference | paragraph | left |  | `{'eastAsia': '黑体'}` | `{'before': '280'}` | `{}` |
| 129 | Text of Reference 1 | paragraph | both | 7.5 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '宋体', 'cs': 'Times New Roman'}` | `{'line': '260', 'lineRule': 'exact'}` | `{}` |
| 130 | 中文参考文献 | paragraph |  |  | `{}` | `{'before': '240'}` | `{}` |
| 132 | Text of 中文参考文献 | paragraph |  |  | `{}` | `{}` | `{'left': '258', 'hanging': '258', 'hangingChars': '258'}` |
| 133 | Text of 中文参考文献１ | paragraph |  |  | `{}` | `{}` | `{}` |
| 145 | 样式1 | paragraph |  |  | `{}` | `{}` | `{'firstLine': '432', 'firstLineChars': '200'}` |
| 149 | 图说明-两端 | paragraph | both | 9.0 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '黑体', 'cs': 'Times New Roman'}` | `{}` | `{}` |
| 154 | 图目录 | paragraph | center | 12.0 | `{'ascii': 'Times New Roman', 'hAnsi': 'Times New Roman', 'eastAsia': '宋体', 'cs': 'Times New Roman'}` | `{'line': '300', 'lineRule': 'auto'}` | `{}` |
| 159 | Title1 | paragraph |  | 12.0 | `{'eastAsia': '黑体'}` | `{'before': '240', 'after': '100'}` | `{}` |
| 173 | 标题 Char | character |  | 16.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'cs': 'Arial'}` | `{}` | `{}` |
| 183 | 文档结构图 Char1 | character |  | 9.0 | `{}` | `{}` | `{}` |
| 184 | 信息标题 Char | character |  | 12.0 | `{'ascii': 'Arial', 'hAnsi': 'Arial', 'cs': 'Arial'}` | `{}` | `{}` |
| 188 | 注释标题 Char | character |  | 9.0 | `{}` | `{}` | `{}` |
| 203 | 标题 1 Char | character |  | 22.0 | `{}` | `{}` | `{}` |
| 204 | 标题 2 Char | character |  | 9.0 | `{'eastAsia': '黑体', 'cs': 'Times New Roman'}` | `{}` | `{}` |
| 207 | 图题 | paragraph | center |  | `{'hAnsi': '宋体'}` | `{'line': '0', 'lineRule': 'atLeast'}` | `{'firstLine': '200', 'firstLineChars': '200'}` |
| 208 | 图题 Char | character |  | 9.0 | `{'hAnsi': '宋体'}` | `{}` | `{}` |
| 209 | EndNote Bibliography Title | paragraph | center | 10.0 | `{'ascii': 'Calibri', 'hAnsi': 'Calibri'}` | `{}` | `{'firstLine': '200', 'firstLineChars': '200'}` |
| 210 | EndNote Bibliography Title Char | character |  |  | `{'ascii': 'Calibri', 'hAnsi': 'Calibri', 'cs': 'Calibri'}` | `{}` | `{}` |
| 213 | 1级标题 | paragraph |  | 10.5 | `{'eastAsia': '黑体'}` | `{'before': '160', 'after': '160'}` | `{}` |
| 214 | 1级标题 Char | character |  | 10.5 | `{'eastAsia': '黑体'}` | `{}` | `{}` |
| 215 | 2级标题 | paragraph | left |  | `{'eastAsia': '黑体'}` | `{'before': '25', 'beforeLines': '25', 'after': '25', 'afterLines': '25'}` | `{}` |
| 216 | 2级标题 Char | character |  | 9.0 | `{'eastAsia': '黑体'}` | `{}` | `{}` |
| 217 | 3级标题 | paragraph | left |  | `{}` | `{}` | `{}` |
| 218 | 3级标题 Char | character |  | 9.0 | `{}` | `{}` | `{}` |
| 222 | 标题1 | paragraph |  | 12.0 | `{'eastAsia': '黑体'}` | `{'before': '240', 'after': '100'}` | `{}` |
| 224 | 标题2 | paragraph |  | 12.0 | `{'eastAsia': '黑体'}` | `{'before': '240', 'after': '100'}` | `{}` |
| 225 | 参考文献 | paragraph |  |  | `{'eastAsia': '方正书宋简体'}` | `{'line': '295', 'lineRule': 'auto'}` | `{}` |
| 229 | 文档结构图 Char | character |  | 9.0 | `{'ascii': '宋体'}` | `{}` | `{}` |

## 4. 段落类别统计

| 类别 | 数量 |
|------|------|
| body_or_heading | 162 |
| figure_caption | 9 |
| table_caption | 3 |
| abstract | 2 |
| keywords | 2 |
| citation_format | 2 |
| reference_heading | 2 |
| reference_item | 1 |

## 5. 首页与正文前 40 个非空段落

| # | 类别 | styleId | 格式 | 文本摘录 |
|---|------|---------|------|----------|
| 1 | body_or_heading | 4 | `{'jc': None, 'spacing': {'line': '0', 'lineRule': 'atLeast'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': 7.5}` | 软件学报ISSN 1000-9825, CODEN RUXUEWE-mail: jos@iscas.ac.cn |
| 2 | body_or_heading | 4 | `{'jc': None, 'spacing': {'line': '0', 'lineRule': 'atLeast'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': 7.5}` | Journal of Software, [doi: 10.13328/j.cnki.jos.000000]http://www.jos.org.cn |
| 3 | body_or_heading | 4 | `{'jc': None, 'spacing': {'line': '0', 'lineRule': 'atLeast'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': 7.5}` | ©中国科学院软件研究所版权所有.Tel: +86-10-62562563 |
| 5 | body_or_heading | 64 | `{'jc': None, 'spacing': {'before': '0', 'line': '0', 'lineRule': 'atLeast'}, 'ind': {}, 'size': 14.0}` | 基于变分自编码器的异构缺陷预测特征表示方法 |
| 6 | body_or_heading | 65 | `{'jc': None, 'spacing': {}, 'ind': {}, 'size': 12.0}` | 贾修一1,  张文舟1,  李伟湋2,  黄志球3 |
| 7 | body_or_heading | 66 | `{'jc': None, 'spacing': {}, 'ind': {'left': '116', 'hanging': '116'}, 'size': 8.0}` | 1(南京理工大学 计算机科学与工程学院,江苏 南京  210094) |
| 8 | body_or_heading | 66 | `{'jc': None, 'spacing': {}, 'ind': {'left': '116', 'hanging': '116'}, 'size': 8.0}` | 2(南京航空航天大学 航天学院,江苏 南京  210016) |
| 9 | body_or_heading | 66 | `{'jc': None, 'spacing': {}, 'ind': {'left': '116', 'hanging': '116'}, 'size': 8.0}` | 3(南京航空航天大学 计算机科学与技术学院,江苏 南京  211106) |
| 10 | body_or_heading | 66 | `{'jc': None, 'spacing': {}, 'ind': {'left': '116', 'hanging': '116'}, 'size': 8.0}` | 通讯作者: 李伟湋, E-mail: liweiwei@nuaa.edu.cn |
| 12 | abstract | 117 | `{'jc': None, 'spacing': {}, 'ind': {}, 'size': None}` | 摘  要:跨项目软件缺陷预测技术可以利用现有的已标注缺陷数据集对新的无标记项目进行预测,但需要两者之间具有相同的度量集合,难以用于实际开发.异构缺陷预测技术可以 |
| 13 | keywords | 118 | `{'jc': None, 'spacing': {}, 'ind': {'left': '798', 'hanging': '798'}, 'size': None}` | 关键词:异构缺陷预测;变分自编码器;特征表示 |
| 14 | body_or_heading | 120 | `{'jc': None, 'spacing': {'before': '0'}, 'ind': {}, 'size': 9.0}` | 中图法分类号:TP311 |
| 15 | citation_format | 121 | `{'jc': 'both', 'spacing': {'after': '0'}, 'ind': {}, 'size': 8.0}` | 中文引用格式: 贾修一,张文舟,李伟湋,黄志球.基于变分自编码器的异构缺陷预测特征表示方法.软件学报,2021,32(7). http://www.jos.or |
| 16 | citation_format | 112 | `{'jc': None, 'spacing': {'before': '57', 'beforeLines': '20', 'line': '0', 'lineRule': 'atLeast'}, 'ind': {'left': '0', 'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 英文引用格式: Jia XY, Zhang WZ, Li WW, Huang ZQ. Feature representation method for het |
| 17 | body_or_heading | 120 | `{'jc': None, 'spacing': {}, 'ind': {}, 'size': 10.5}` | Feature Representation Method for Heterogeneous Defect Prediction Based on Varia |
| 18 | body_or_heading | 121 | `{'jc': None, 'spacing': {'before': '100', 'after': '100'}, 'ind': {}, 'size': None}` | JIA Xiu-Yi1,  ZHANG Wen-Zhou1,  LI Wei-Wei2,  HUANG Zhi-Qiu3 |
| 19 | body_or_heading | 112 | `{'jc': None, 'spacing': {'line': '240', 'lineRule': 'exact'}, 'ind': {'left': '103', 'hanging': '103'}, 'size': 7.5}` | 1(School of Computer Science and Engineering, Nanjing University of Science and  |
| 20 | body_or_heading | 112 | `{'jc': None, 'spacing': {'line': '240', 'lineRule': 'exact'}, 'ind': {'left': '103', 'hanging': '103'}, 'size': 7.5}` | 2(College of Aerospace Engineering, Nanjing University of Aeronautics and Astron |
| 21 | body_or_heading | 112 | `{'jc': None, 'spacing': {'line': '240', 'lineRule': 'exact'}, 'ind': {'left': '103', 'hanging': '103'}, 'size': 7.5}` | 3(College of Computer Science and Technology, Nanjing University of Aeronautics  |
| 22 | abstract | 115 | `{'jc': None, 'spacing': {'before': '142', 'beforeLines': '50', 'line': '234', 'lineRule': 'exact'}, 'ind': {}, 'size': 7.5}` | Abstract:  Cross-project defect prediction technology can use the existing label |
| 23 | keywords | 113 | `{'jc': None, 'spacing': {}, 'ind': {'left': '1162', 'hanging': '1162', 'firstLineChars': '0'}, 'size': 7.5}` | Key words:  heterogeneous defect prediction; variational autoencoders; feature r |
| 24 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 软件缺陷预测技术是软件质量保证活动中非常重要的研究课题,基于机器学习方法进行缺陷预测可以从历史项目数据中学到软件度量和软件缺陷之间的联系,有效地帮助开发人员和测 |
| 25 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 现有的基于机器学习方法的软件缺陷预测模型需要首先设计衡量模块复杂度的度量并收集相关的缺陷数据集,之后才能在缺陷数据集上训练预测模型[2].大部分缺陷度量分为基于 |
| 27 | figure_caption | 4 | `{'jc': 'center', 'spacing': {'after': '142', 'afterLines': '50'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 图1  跨项目软件缺陷预测和异构软件缺陷预测 |
| 28 | body_or_heading | 145 | `{'jc': 'distribute', 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 大部分跨项目缺陷预测方法有一个严重的限制,即需要源项目和目标项目具有相同的软件度量[9],然而在现实情况下,大部分项目都具有异构的特征表示.例如,在PROMIS |
| 29 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 元[5],AEEEM数据集拥有61个度量元[8],它们之间唯一相同的度量是代码行数(LOC).由于公有度量的匮乏,现有的跨项目软件缺陷预测方法将难以适用,并且, |
| 30 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 对于异构缺陷预测研究,该问题的主要难点有:(1) 源项目和目标项目的度量没有相同的语义,除了少数度量相同之外,大部分都没有任何对应关系.(2) 不同项目之间由于 |
| 31 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 针对上述问题,本文提出了一种基于变分自编码器的特征迁移映射方法T-VAE(transfer-variational autoencoder),可以将源项目与目标 |
| 33 | figure_caption | 4 | `{'jc': 'center', 'spacing': {'after': '142', 'afterLines': '50'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 图2  基于变分自编码器的异构缺陷预测模型框架图 |
| 34 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 本文第1节介绍异构缺陷预测的相关方法和研究现状.第2节介绍本文所需的基础知识,包括变分自编码器和最大均值差异.第3节介绍本文构建的基于变分自编码器的异构缺陷预测 |
| 35 | body_or_heading | 3 | `{'jc': None, 'spacing': {}, 'ind': {}, 'size': None}` | 异构缺陷预测相关工作 |
| 36 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 现有的软件缺陷预测模型大多数都基于机器学习方法且集中于项目间软件缺陷预测.然而,对于新的项目而言,其历史缺陷数据是非常稀缺的,并且软件开发方法和语言的更新迭代十 |
| 37 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '380'}, 'size': None}` | 异构缺陷预测是指使用从其他项目收集的异构度量数据来预测目标项目中软件实例的缺陷倾向性.它为缺陷预测提供了一个新的视角.最近,有相关工作提出了几种异构缺陷预测模型 |
| 38 | body_or_heading | 3 | `{'jc': None, 'spacing': {}, 'ind': {}, 'size': None}` | 基础知识 |
| 39 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 本文所提方法主要基于变分自编码器和最大均值差异,下面就相关概念和基本知识予以介绍. |
| 40 | body_or_heading | 5 | `{'jc': None, 'spacing': {'before': '71', 'after': '71'}, 'ind': {}, 'size': None}` | 变分推断和变分自编码器 |
| 41 | body_or_heading | 145 | `{'jc': 'distribute', 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | 对于常见的缺陷度量数据,可以假设它们是由更高层的变量生成,并且这些隐变量满足特定的分布,一般代表着数据的内在结构或者某种抽象.例如,缺陷数据集可以看作是由度量代 |
| 42 | body_or_heading | 145 | `{'jc': 'distribute', 'spacing': {'line': '0', 'lineRule': 'atLeast'}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 度等隐式特征生成的数据.假设原始缺陷数据集为包含N个独立同分布的连续变量x,这些数据是利 |
| 43 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '0', 'firstLineChars': '0'}, 'size': None}` | 用未观测到的隐变量z通过某些随机过程而生成.这个过程一般包含两个步骤. |
| 44 | body_or_heading | 145 | `{'jc': None, 'spacing': {}, 'ind': {'firstLine': '372'}, 'size': None}` | (1) 从隐变量所服从分布p(z)的概率密度函数中生成一个值zi; |

## 6. 图表题注段落

| # | 类型 | styleId | 对齐 | 段前/段后/行距 | 文本 |
|---|------|---------|------|----------------|------|
| 27 | figure_caption | 4 | center | `{'after': '142', 'afterLines': '50'}` | 图1  跨项目软件缺陷预测和异构软件缺陷预测 |
| 33 | figure_caption | 4 | center | `{'after': '142', 'afterLines': '50'}` | 图2  基于变分自编码器的异构缺陷预测模型框架图 |
| 65 | figure_caption | 145 | center | `{'after': '85', 'afterLines': '30'}` | 图3  变分自编码器 |
| 71 | figure_caption | 145 | center | `{'after': '142', 'afterLines': '50'}` | 图4  利用最大均值差异学习分布 |
| 90 | figure_caption | (none) | center | `{}` | 图5  基于变分自编码器的异构特征映射(源项目与目标项目共同训练网络) |
| 111 | table_caption | 4 | center | `{}` | 表1  实验数据集 |
| 133 | table_caption | 4 | center | `{'before': '142', 'beforeLines': '50', 'after': '142', 'afterLines': '50'}` | 表2  T-VAE与项目间和跨项目缺陷预测方法性能比较 |
| 141 | table_caption | 4 | center | `{'before': '142', 'beforeLines': '50', 'after': '142', 'afterLines': '50'}` | 表3  T-VAE与异构缺陷预测方法性能比较 |
| 145 | figure_caption | 145 |  | `{}` | 图6~图8分别展示了不同损失项在不同权重下的性能表现.从图中可以看出,即使是相同的数据集,不同的损失权重也会导致有很大的差异,因此选择一个合适的参数对于获得有效的最终分类性能而言是非常重要的,例如,P |
| 150 | figure_caption | 4 | center | `{'before': '142', 'beforeLines': '50', 'after': '142', 'afterLines': '50'}` | 图6  在给定最大均值差异和分类损失权重情况下,先验分布差异在不同权重下的性能变化 |
| 153 | figure_caption | 4 | center | `{'after': '142', 'afterLines': '50'}` | 图7  在给定先验分布差异和分类损失权重情况下,最大均值差异在不同权重下的性能变化 |
| 156 | figure_caption | 4 | center | `{'after': '142', 'afterLines': '50'}` | 图8  在给定先验分布差异和最大均值差异权重情况下,分类损失在不同权重下的性能变化 |

## 7. 参考文献段落

| # | 类别 | styleId | 缩进 | 行距 | 文本摘录 |
|---|------|---------|------|------|----------|
| 160 | reference_heading | 126 | `{}` | `{}` | References |
| 190 | reference_heading | 130 | `{}` | `{}` | 附中文参考文献 |
| 191 | reference_item | 132 | `{'left': '378', 'hanging': '377', 'hangingChars': '242'}` | `{}` | [2]陈翔,顾庆,刘望舒,刘树龙,倪超.静态软件缺陷预测方法研究.软件学报,2016,27(1):1−25. http://www.jos.org.cn/1000-9825/4923. htm [do |

## 8. 媒体与嵌入对象

- 媒体文件数：79
- OLE 嵌入对象数：71

完整机器可读定义见：`docs/format/jos_2025_docx_format_definitions.json`。
