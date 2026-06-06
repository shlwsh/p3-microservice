---
name: paper1-multi-agent-review
description: >-
  Simulates multi-role peer review of the p3-microservice Chinese LaTeX
  manuscript (distributed directed log collection): precheck, blind review,
  cross-examination, PI synthesis, writes reports under reviews/{run_id}/.
  Self-contained skill pack. Use when the user asks to review the p3 paper,
  run multi-agent paper review, 执行论文多角色审核, 软件学报投稿前审核,
  论文审核, compare against benchmark JOS papers, run major-revision closure,
  or simulate peer reviewers.
disable-model-invocation: false
---

# p3 论文多智能体交互式审核

**本技能包自包含**：执行前阅读 [config.md](config.md)；**各角色勾选清单**见 [审核细则.md](审核细则.md)。  
**投《软件学报》**：必读 [软件学报投稿要点.md](软件学报投稿要点.md)，`TARGET_JOURNAL=JOS`（config 默认）。

## 启动时必读（按序）

1. [config.md](config.md) — 路径、**TARGET_JOURNAL**、JOS 文献门槛  
2. [审核细则.md](审核细则.md) — **Phase 1–2 各角色细则（优先）**  
3. [软件学报投稿要点.md](软件学报投稿要点.md) — **JOS 初审/退稿高发区（JOS 时必读）**  
4. [参考文献归档细则.md](参考文献归档细则.md) — **C6 文献核实与 `papers/` 归档**  
5. [已知问题清单.md](已知问题清单.md) — C1–C6 + **J1–J7**  
6. [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) — **论文 A/B 八维度对照、重大修改、二次评审、版本化编译**
7. [论文领域要点.md](论文领域要点.md) — SQ、基线、国内文献方向
8. [角色定义手册.md](角色定义手册.md) — 扮演语气与职责

## 使用时机

- **执行 p3 论文多角色审核** / **软件学报投稿前审核** / **模拟审稿人**
- 投稿《软件学报》（默认）或《计算机学报》前要 P0/P1/P2 行动清单
- 对照基准论文 A（包航宇等，2023）与论文 B（贾统等，2020）做重大修改闭环
- 根据评审意见生成 `docs/YYYYMMDD-HHMMSS-*.md` 方案、修改主稿、编译版本化 PDF、二次评审
- **默认不改 `.tex`**（改稿见 [改稿衔接.md](改稿衔接.md)）

## 路径（来自 config.md）

| 项 | p3 默认 |
|----|---------|
| `PAPER1_ROOT` | `.`（仓库根） |
| 主稿 LaTeX | `latex/main-zh.tex`、`latex/main-jos.tex` |
| 主稿 Markdown | `docs/v4-论文稿件.md` |
| L0 真相 | `experiments/results/phase3/phase3_latest.json` |
| 输出 | `reviews/{run_id}/` |
| 改稿方案/二评 | `docs/{timestamp}-*.md` |
| 版本化文稿 | `docs/v{N}-论文稿件-jos-{timestamp}.pdf` |

## 执行承诺

1. 完成 Phase 0→5，落盘 **12 个文件**（见 [reference.md](reference.md)）  
2. 盲审互不可见；Phase 3 后再交叉引用  
3. Major 问题含 `tex`/`md` 路径或 L0 JSON 字段证据  
4. 数值以 **phase3 JSON** 为准，禁止编造  
5. 对话末尾贴执行摘要 + 主报告路径  
6. 中文撰写（引文可英文）

## 任务清单

```text
Phase 0  🎯 → 00-上下文清单.md
Phase 1  📚 → 01-预检报告.md        （C1–C6 + JOS 时 J1–J7；**跑 verify_cited_papers.py**）
Phase 2  🔍 → 02-审稿人A-方法论.md  （按 审核细则 §2）
Phase 2  🔬 → 02-审稿人B-领域.md    （按 审核细则 §3）
Phase 2  📊 → 02-统计审查.md        （按 审核细则 §4）
Phase 2  ✍️ → 02-编辑审查.md        （按 审核细则 §5）
Phase 2  📐 → 02-伦理审查.md        （按 审核细则 §6）
Phase 3      → 03-交互质询纪要.md   （议题簇见 审核细则 §7）
Phase 4  🎓 → 04-PI综合裁决.md + 行动清单.md
Phase 5  🎯 → 05-全面评审报告.md + 执行摘要.md
```

## 分阶段要点

**Phase 0**：列 `latex/sections/zh/*.tex` 行数；读 `phase3_latest.json` 摘要字段；列 Markdown/LaTeX 双主稿；写 `00-上下文清单.md`。

**Phase 1**：**先跑** `python3 scripts/verify_cited_papers.py --download`（C6）；再 `grep ±1000`、J1–J7。

**Phase 5**：`05` 附录含 JOS 投稿外 checklist + `cited_papers_manifest.json` 摘要。

**Phase 2**：五角色**按审核细则勾选**，勿重复通读全文；Issue 前缀 `METHOD-` `DOMAIN-` `STAT-` `EDIT-` `ETHICS-`。**新增维度**：方法论检查伪代码完整性（M7）、多规模实验（M10）、量化创新对比（MJ4）；领域检查 2023+ 前沿覆盖（D6-D8）、对比表扩展（DJ6）、三贡献贯穿（DJ7）；统计检查图文一致（S10）、误差条（S7）；编辑检查英文术语统一（E12）、长句（E13）。

**Phase 3**：Top-3 分歧（CL-FAIR / CL-SIGMA / CL-SYNC 等）；对话体；`[共识]` / `[交 PI 裁决]`。

**Phase 4**：PI 决定 + P0≤7 的 `行动清单.md`（含验收标准、需同步文件）。

**Phase 5**：合并 [设计方案.md §5.7](设计方案.md) → `05-全面评审报告.md`。

## DoD

- [ ] `reviews/{run_id}/` 下 12 文件齐全  
- [ ] `05` 含综合问题清单，P0≤7  
- [ ] ≥80% Major 有 L0/行号证据  
- [ ] C3（数值/σ）已验证；C5（基金/AI）已验证  
- [ ] **C6** 文献归档脚本 exit 0  
- [ ] **C7** 算法伪代码/形式化已评估  
- [ ] **C9** 图表数据与正文一致性已核查  
- [ ] **C10** 创新量化与三贡献贯穿已评估  
- [ ] **（JOS）** J2/J3 国内对比与中文文献已评估  
- [ ] **（JOS）** J8 最新前沿文献覆盖已评估  
- [ ] **（JOS）** J9 英文 Abstract 术语一致性已核查
- [ ] **（JOS）** J11 基准论文 A/B 八维度对照已评估
- [ ] **改稿闭环** 方案文档已输出到 `docs/` 且文件名带时间戳
- [ ] **改稿闭环** 编译稿件已带版本号与时间戳，历史稿未删除
- [ ] **改稿闭环** 修改后已形成二次评审报告
- [ ] 对话已交付执行摘要  

## 快捷命令（p3）

```bash
# 表1 σ 与阶段表述
grep -rn "1000\|±1000" latex/sections/zh/06_experiments.tex docs/v4-论文稿件.md || true
grep -rn "首期" docs/v4-论文稿件.md latex/sections/zh/ || true

# 结构篇幅
wc -l latex/sections/zh/*.tex

# L0 主结论
python3 -c "import json; d=json.load(open('experiments/results/phase3/phase3_latest.json')); c=d.get('comparison',d); print(c.get('reduction_percent',{}).get('log_volume'), c.get('full_collect',{}).get('log_volume_stdev'))"

# 非学术段 / 基金占位
grep -Ei 'faq|基金项目|待填' latex/ docs/v4-论文稿件.md 2>/dev/null || true

# JOS：中文文献占比 + 营销语
python3 -c "import re,pathlib;b=pathlib.Path('latex/references.bib').read_text(encoding='utf-8',errors='ignore');es=re.split(r'@\w+\{',b)[1:];zh=sum(1 for e in es if re.search(r'[\u4e00-\u9fff]',e) or '软件学报' in e or '计算机学报' in e);print('zh-ish',zh,'/',len(es))"
grep -Ein '本产品|国内领先|唯一' latex/sections/zh/ docs/v4-论文稿件.md 2>/dev/null || true

# C6 正文引用文献核实与归档
python3 scripts/verify_cited_papers.py --download
```

## 技能包文档索引

| 文件 | 用途 |
|------|------|
| [审核细则.md](审核细则.md) | **各角色高效勾选清单** |
| [参考文献归档细则.md](参考文献归档细则.md) | **C6 文献核实与 papers/ 归档** |
| [软件学报投稿要点.md](软件学报投稿要点.md) | **JOS 官网投稿与敬告作者** |
| [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) | **论文 A/B 对比、重大修改闭环、二次评审** |
| [README.md](README.md) | 复制到其他项目 |
| [设计方案.md](设计方案.md) | 完整 Phase 流程 |
| [reference.md](reference.md) | 模板速查 |
| [改稿衔接.md](改稿衔接.md) | 审核后改稿 |
