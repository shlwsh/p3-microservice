# LaTeX 目录结构、文件作用与关联性分析文档

本文档对本项目中的 `latex` 目录及相关编译脚本、排版模板进行全面深入的分析，理清各模块文件在学术论文写作与技术方案呈现中的具体作用，并梳理它们与 Go 原型系统代码、实验验证脚本之间的映射关系。

---

## 1. 整体目录树结构

`latex` 目录是论文稿件的核心编写区，其结构设计遵循多模板共享、章节分离的原则。以下是与 LaTeX 编写、编译及模板直接相关的目录树：

```
/root/work/p3-microservice/
├── latex/                              # LaTeX 项目主目录
│   ├── .latexmkrc                      # Latexmk 编译配置文件
│   ├── main-zh.tex                     # 中文初稿主入口（计算机学报/CTeX 通用格式）
│   ├── main-jos.tex                    # 软件学报排版稿主入口
│   ├── rjthesis.cls                    # 软件学报 LaTeX 样式模板定义文件
│   ├── references.bib                  # 参考文献 BibTeX 数据库（共 51 篇文献）
│   └── sections/
│       └── zh/                         # 中文章节源文件目录
│           ├── 01_intro.tex            # 引言（背景、科学问题、科学假设与贡献）
│           ├── 02_related.tex          # 相关工作（现状综述、对比表）
│           ├── 03_system.tex           # 系统总体设计（三层架构与工作流）
│           ├── 04_algorithms.tex       # 关键算法（形式化描述与公式）
│           ├── 05_implementation.tex   # 系统实现（技术选型与部署配置）
│           ├── 06_experiments.tex      # 实验与分析（数据支撑、消融实验与基线对照）
│           └── 07_conclusion.tex       # 结束语（贡献总结与未来展望）
├── scripts/                            # 编译与辅助脚本目录
│   ├── build_pdf.sh                    # 编译 main-zh.tex 生成中文初稿 PDF
│   ├── build_pdf_jos.sh                # 编译 main-jos.tex 生成软件学报格式 PDF
│   └── build_pdf_versioned.sh          # 自动版本化编译并备份至 docs 目录
└── docs/                               # 文档及交付成果目录
    └── latex-models/                   # 学术期刊官方原始排版模板
        └── software-journal/           # 《软件学报》官方原始模板
            └── rjthesis.cls            # 模板类文件源文件
```

---

## 2. 核心入口文件作用详解

### 2.1 [main-zh.tex](file:///root/work/p3-microservice/latex/main-zh.tex) (中文初稿主入口)
* **作用**：该文件是采用标准 `ctexart` 宏包编写的中文学术论文初稿入口文件（排版风格接近《计算机学报》）。它规定了双栏/单栏排版的页面几何尺寸、字体配置，并提供中英文双语标题、摘要及关键词的声明。
* **引入模块**：通过 `\input{sections/zh/01_intro.tex}` 等命令按顺序动态引入 7 个子章节，并使用 `\bibliography{references}` 引入参考文献数据库。
* **样式特征**：使用标准的 LaTeX 宏包（如 `geometry`, `graphicx`, `amsmath`, `booktabs`, `algorithm2e` 等），便于在 Overleaf 或本地 TeX Live 环境中进行通用编译。

### 2.2 [main-jos.tex](file:///root/work/p3-microservice/latex/main-jos.tex) (软件学报排版稿主入口)
* **作用**：该文件是专门针对《软件学报》格式要求调整的排版稿主入口文件。它使用自定义的文档类 `rjthesis.cls`。
* **定制机制**：
  * 使用系统 Noto CJK 字体，通过 `\PassOptionsToClass{fontset=ubuntu,twoside,UTF8}{ctexart}` 规避 Fandol 字体引起的 `Script=CJK` 警告。
  * 提供特定宏命令的兼容性兜底（如 Ubuntu 字体集缺少仿宋和隶书时，将 `\fangsong` 映射为 `\kaishu`，将 `\lishu` 映射为 `\songti`）。
  * 声明学报专用的元数据字段：`\rjhead`（页眉页脚作者简称）、`\rjtitle`（正文大标题）、`\rjauthor`（作者列表）、`\rjinfor`（单位与通讯作者信息）、`\begin{rjabstract}` 与 `\end{rjabstract}`（学报专用摘要环境）。
* **引入模块**：与 [main-zh.tex](file:///root/work/p3-microservice/latex/main-zh.tex) 共享相同的物理章节文件（`sections/zh/*.tex`），实现了**“内容与排版样式分离”**的高效管理模式。

---

## 3. 模板与配置文件分析

### 3.1 [rjthesis.cls](file:///root/work/p3-microservice/latex/rjthesis.cls) (软件学报模板类文件)
* **作用**：它是《软件学报》官方排版格式的 LaTeX 类定义文件。该文件定义了页边距、双栏宽度、行距、标题字号、摘要框样式、以及图表标题（Caption）的专有中英文双语字体字号规范。
* **与 docs 的关联**：它是从官方模板库 [docs/latex-models/software-journal/rjthesis.cls](file:///root/work/p3-microservice/docs/latex-models/software-journal/rjthesis.cls) 复制或链接过来的，以确保编译时 LaTeX 能在当前路径直接加载它。

### 3.2 [.latexmkrc](file:///root/work/p3-microservice/latex/.latexmkrc) (Latexmk 配置文件)
* **作用**：规定了自动编译工具 `latexmk` 的执行行为。
* **核心配置**：
  * `$pdf_mode = 5;`：指定使用 `xelatex` 引擎作为主要的 PDF 生成器（因为中文稿件中的 `ctex` 宏包和中文字体必须依赖 XeLaTeX 进行渲染，普通的 `pdflatex` 无法加载）。
  * `$bibtex_use = 2;`：配置在交叉引用或文献发生变化时自动调用 `bibtex` 编译。
  * `TEXINPUTS` 环境变量追加：将类文件搜索路径延伸至 `../docs/latex-models/software-journal//`，这样即使在 `latex` 根目录下没有放置 `rjthesis.cls`，编译引擎也能自动向上检索并成功加载学报模板类。

### 3.3 [references.bib](file:///root/work/p3-microservice/latex/references.bib) (参考文献数据库)
* **作用**：集中管理整篇论文引用的所有文献条目。
* **内容构成**：共包含 **51 篇学术文献**，严格覆盖以下关键研究领域：
  * **智能运维与故障诊断**：如包航宇等 `bao2023aiops`（AIOps 标准化）、贾统等 `jiatong2020logdiag`（日志故障诊断综述）。
  * **云原生可观测性与日志管理**：如 `otel_tail`（OpenTelemetry 尾部采样）、`usman2022observability`（容器微服务遥测综述）、`soldani2023ebpf`（eBPF 可观测性）。
  * **网络重试与系统优化**：涵盖指数退避机制在分布式环境下的理论支撑。

---

## 4. 章节文件（sections/zh/）内容及核心概念分析

### 4.1 [01_intro.tex](file:///root/work/p3-microservice/latex/sections/zh/01_intro.tex) (引言)
* **核心内容**：阐述分布式微服务架构下全量日志采集面临的瓶颈问题（网络带宽、计算资源与存储开销）。
* **理论框架**：
  * **科学问题**：如何在不侵入业务、不改变调用链的条件下，将网关流量异常信号转化为节点侧应用日志采集约束。
  * **研究问题与假设**：明确提出并映射四个子研究问题（RQ1--RQ4）和科学假设（H1--H4），为第 6 节的实验提供逻辑对应。
  * **主要贡献**：概括了三层分布式定向采集框架、关键算法的形式化及 WSL/Docker 容器集群的实测与多进程仿真验证成果。

### 4.2 [02_related.tex](file:///root/work/p3-microservice/latex/sections/zh/02_related.tex) (相关工作)
* **核心内容**：对集中式日志栈、调用链采样与追踪关联、边缘采集、日志解析与故障诊断进行现状综述。
* **代表性对比表**：包含表 `tab:related_compare`，在策略输入、减量位置、日志削减证据、Sidecar 开销等维度，将本文方案与标准 ELK/EFK、Loki/Promtail 静态过滤、OTel 尾部采样及 eBPF 日志采集进行了量化比对，突出了本方案“采集前端定向减量”的定位。

### 4.3 [03_system.tex](file:///root/work/p3-microservice/latex/sections/zh/03_system.tex) (系统总体设计)
* **核心内容**：定义系统的整体架构。
* **架构划分**：
  * **网关预筛选层**：基于 Nginx/OpenResty Lua 从南北向入口流量中预筛选异常及慢请求。
  * **节点定向采集层**：各服务节点上的 Sidecar Agent 根据动态下发的关注清单，在本地过滤应用日志。
  * **中心二次过滤层**：日志中心 Center 聚合数据，过滤过期或重复批次，最终存入 Loki 存储层。
* **关键插图**：引用 `fig1_system_overview.pdf`，以直观图示呈现 Agent 与 Center 之间的数据流和控制流。

### 4.4 [04_algorithms.tex](file:///root/work/p3-microservice/latex/sections/zh/04_algorithms.tex) (关键算法)
* **核心内容**：提供了系统四大核心机制的形式化描述与数学公式：
  1. **关注清单动态生成算法**（算法 1 `alg:attention`）：
     * 输入时间窗内的网关流量日志集合 $L$，利用 URL 泛化函数（提取 ID 和 UUID 等变量）聚类。
     * 权重计算公式：
       $$w_p = \alpha \cdot \text{count} + \beta \cdot \text{severity}$$
     * 利用 Top-$K$ 堆排序或全量排序，生成带有 TTL（生存时间）的高价值关注清单。
  2. **固定缓存块机制**：描述环形缓存队列的设计，提供双重容量约束（字节数与条目数）和 FIFO 淘汰策略，保障内存空间有界。
  3. **定向策略三次转换算法**：通过网关预筛选、节点定向匹配和中心二次过滤之间的三次策略映射（引入同一版本号 $v$），确保跨层语义一致。
  4. **压力感知指数退避算法**（公式 1）：
     $$d_n = \min\bigl(d_{\max},\, d_0\rho^n + \text{rand}(0,\, d_0\rho^n\xi)\bigr)$$
     * 参数定义：$d_0=200\text{ ms}$（基准延迟），$\rho=2.0$（指数因子），$d_{\max}=30\text{ s}$（等待时间上限），$\xi=0.3$（随机抖动）。
     * 特殊逻辑：检测到节点处于资源高压状态时，退避延迟翻倍；超过 6 次重试上限后，未上传成功的日志写入本地 BoltDB 兜底。

### 4.5 [05_implementation.tex](file:///root/work/p3-microservice/latex/sections/zh/05_implementation.tex) (系统实现)
* **核心内容**：详述原型系统的工程选型（Go 1.22、gRPC+Protobuf、Redis、Loki、OpenResty + Lua、BoltDB）。
* **架构划分**：将 Agent 划分为采集、匹配、缓存、重试、上传和监控子模块；将 Center 划分为清单生成、接收过滤、存储推送和配置分发子模块。
* **部署配置**：说明了 Docker Compose 集群配置、WSL 下的内存资源限制、以及在 Kubernetes 中的生产部署规范（如 TLS 加密、多租户策略隔离）。

### 4.6 [06_experiments.tex](file:///root/work/p3-microservice/latex/sections/zh/06_experiments.tex) (实验与分析)
* **核心内容**：给出整篇论文最具说服力的实测与模拟实验数据支撑。
* **关键实验发现**：
  * **主对比实验**（表 `tab:compare` & 图 `fig:compare`）：定向采集模式将 Loki 的入库日志量从全量基线的 4388 条降至 72 条，相对降低 **98.4%**；Agent 平均 CPU 相对降低 **37.5%**（绝对值低至 0.05%）；内存占用相近。
  * **多进程模拟**（同频对照）：通过同频率（2\,s）模拟，排除了原稿中全量模式发射频率较快的影响，计算出策略过滤的独立相对降幅为 **67.8%**。
  * **规模扩展实验**（图 `fig:scale`）：清空历史计数后，进行了 16 和 32 微服务节点的实测复核，验证了在大规模节点下，Loki 的入库量依然处于低位且平稳（16 节点入库为 48.0 条，32 节点入库为 99.0 条，Agent 资源均保持极低开销）。
  * **消融实验**（图 `fig:ablation`）：关闭“关注清单”导致 Loki 入库量激增 **211.7%**，证明清单匹配是减量的绝对核心机制。
  * **时效性与可靠性**：端到端延迟 P50 为 0.83\,s，P95 为 12\,s，符合业界日志采集的标准要求；并提供了中心宕机恢复（故障时间 1.1\,s）的弹性数据。
  * **工业基线对照**（图 `fig:baseline`）：将本方案与 Promtail 静态过滤（入库 276.3 条 vs 本方案 233.3 条）、OTel 尾部采样、eBPF 日志过滤进行了多层次对比。

### 4.7 [07_conclusion.tex](file:///root/work/p3-microservice/latex/sections/zh/07_conclusion.tex) (结束语)
* **核心内容**：提炼论文的核心学术与工程价值，并明确指出近期工作（64 节点云原生实测、Top-$K$ 敏感性分析）、中期工作（真实微服务负载验证、经济成本模型构建）和远期工作（追踪上下文与内核探针闭环、生产安全加固与 JSON 标准制定）的后续研究方向。

---

## 5. LaTeX 章节内容与底层 Go 代码包/脚本映射关系

为了在修改代码或更新论文数据时能够做到双向追溯，以下整理了 LaTeX 论文中的理论描述与项目中实际物理代码文件之间的映射关系：

| 章节与模块 | 论文中提到的名称/概念 | 项目中实际对应的代码文件 / 数据结果路径 |
| :--- | :--- | :--- |
| **Agent 重试模块** | 压力感知指数退避公式 ($d_n$) 与单测 | [agent/pkg/retry/backoff.go](file:///root/work/p3-microservice/agent/pkg/retry/backoff.go)<br>[agent/pkg/retry/backoff_test.go](file:///root/work/p3-microservice/agent/pkg/retry/backoff_test.go) |
| **Agent 缓存模块** | 固定缓存块与环形队列算法 | [agent/pkg/cache/buffer.go](file:///root/work/p3-microservice/agent/pkg/cache/buffer.go) |
| **Agent 匹配模块** | 定向规则与 URL 前缀通配匹配器 | [agent/pkg/matcher/matcher.go](file:///root/work/p3-microservice/agent/pkg/matcher/matcher.go) |
| **Center 核心模块** | 关注清单动态生成算法与规则分发 | [center/pkg/strategy/generator.go](file:///root/work/p3-microservice/center/pkg/strategy/generator.go)<br>[center/pkg/dispatch/dispatcher.go](file:///root/work/p3-microservice/center/pkg/dispatch/dispatcher.go) |
| **通信接口** | gRPC 通信协议与数据结构契约 | [proto/collector.proto](file:///root/work/p3-microservice/proto/collector.proto) |
| **对比实验数据** | 八节点主对比实验原始数据 (180\,s) | [experiments/results/phase3/phase3_latest.json](file:///root/work/p3-microservice/experiments/results/phase3/phase3_latest.json) |
| **规模复核数据** | 16 / 32 节点扩展复核原始数据 | [experiments/results/phase4/phase4_20260611_021230.json](file:///root/work/p3-microservice/experiments/results/phase4/phase4_20260611_021230.json)<br>[experiments/results/phase4/phase4_20260611_024321.json](file:///root/work/p3-microservice/experiments/results/phase4/phase4_20260611_024321.json) |
| **模拟与消融** | 多进程同频模拟与系统组件消融脚本 | [experiments/scripts/phase5_multiprocess_sim.py](file:///root/work/p3-microservice/experiments/scripts/phase5_multiprocess_sim.py)<br>[experiments/results/phase5/phase5_latest.json](file:///root/work/p3-microservice/experiments/results/phase5/phase5_latest.json) |

---

## 6. 论文编译与构建指南

项目提供了完整的 Bash 脚本来自动化处理 LaTeX 的编译过程，避免开发者手动多次运行 `xelatex` 和 `bibtex`。

### 6.1 编译中文初稿 PDF (计算机学报风格)
* **执行脚本**：[scripts/build_pdf.sh](file:///root/work/p3-microservice/scripts/build_pdf.sh)
* **编译逻辑**：
  1. 进入 `latex/` 目录。
  2. 运行第一遍 `xelatex main-zh.tex`，生成交叉引用基础辅助文件 (`main-zh.aux`)。
  3. 运行 `bibtex main-zh` 解析参考文献，生成 `main-zh.bbl`。
  4. 连续运行第二遍和第三遍 `xelatex main-zh.tex`，完成交叉引用、公式编号和参考文献索引列表的最终对齐排版。
* **输出路径**：[latex/main-zh.pdf](file:///root/work/p3-microservice/latex/main-zh.pdf)

### 6.2 编译软件学报排版稿 PDF
* **执行脚本**：[scripts/build_pdf_jos.sh](file:///root/work/p3-microservice/scripts/build_pdf_jos.sh)
* **编译逻辑**：
  1. 检查 `docs/latex-models/software-journal` 下是否存在官方类文件 `rjthesis.cls`。
  2. 将 `TEXINPUTS` 临时追加学报模板搜索路径，并进入 `latex/` 目录。
  3. 执行 XeLaTeX $\rightarrow$ BibTeX $\rightarrow$ XeLaTeX $\times$ 2 编译链，针对 `main-jos.tex` 进行编译。
* **输出与同步**：成功后，会将生成的 PDF 覆盖备份至 [docs/v4-论文稿件-jos.pdf](file:///root/work/p3-microservice/docs/v4-论文稿件-jos.pdf) 中。

### 6.3 自动版本化编译
* **执行脚本**：[scripts/build_pdf_versioned.sh](file:///root/work/p3-microservice/scripts/build_pdf_versioned.sh)
* **使用方式**：`./scripts/build_pdf_versioned.sh [版本号]` (如 `./scripts/build_pdf_versioned.sh 17`)
* **作用**：脚本会顺序调用上述两个编译脚本，并将生成的 `main-jos.pdf` 与 `main-zh.pdf` 自动重命名为带时间戳和版本标签的物理文件并转存到 `docs/` 目录下（如 `docs/v17-论文稿件-jos-20260611-142713.pdf`），实现稿件版本的自动化追溯归档。

### 6.4 编译环境依赖
在编译前，系统需安装以下基础设施：
* **TeX Live 2021+**（需包含 `xeCJK` 与 `ctex` 宏包）。
* Linux 系统下建议安装 `Noto Sans CJK SC` 和 `Noto Serif CJK SC` 字体，以避免 `fontset` 加载警告。
* 确保已安装系统命令 `xelatex` 与 `bibtex`。
