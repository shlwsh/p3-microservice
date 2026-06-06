# 速查与模板

> 完整流程见 [设计方案.md](设计方案.md)。**各角色细则**见 [审核细则.md](审核细则.md)。配置见 [config.md](config.md)。

## 输出文件（12 个）

```
reviews/{run_id}/
├── 00-上下文清单.md
├── 01-预检报告.md
├── 02-审稿人A-方法论.md
├── 02-审稿人B-领域.md
├── 02-统计审查.md
├── 02-编辑审查.md
├── 02-伦理审查.md
├── 03-交互质询纪要.md
├── 04-PI综合裁决.md
├── 05-全面评审报告.md      ★ 主交付物
├── 行动清单.md
└── 执行摘要.md             ★ 对话优先展示
```

## 四稿同步（预检/统计/编辑共用）

| 层级 | 路径 |
|------|------|
| L0 | `experiments/results/phase3/phase3_latest.json` |
| L1 | `docs/验证结果_三期.md` |
| LaTeX | `latex/main-zh.tex`、`latex/sections/zh/*.tex` |
| Markdown | `docs/v4-论文稿件.md` |

## 预检 C1–C6 + J1–J7（JOS）

见 [已知问题清单.md](已知问题清单.md)。**P0 高发**：C3a、C6c、J2/J3。

## 文献归档（C6）

见 [参考文献归档细则.md](参考文献归档细则.md)。命令：

```bash
python3 scripts/verify_cited_papers.py --download
```

## 《软件学报》专检

完整条文见 [软件学报投稿要点.md](软件学报投稿要点.md)。审核产出须在 `05` 附录含 **§10 投稿外 checklist**。

## 交互议题簇（p3 + JOS）

| ID | 主题 | 参与 |
|----|------|------|
| CL-FAIR | 98.4% vs 2s/400ms 发射频率 | 🔍 📊 |
| CL-SIGMA | σ 修正后结论是否成立 | 📊 ✍️ |
| CL-SIM | 图4 仿真 vs 表1 实测 | 🔍 🔬 |
| CL-SYNC | Markdown/LaTeX 以谁为准 | ✍️ 📚 |
| CL-SCOPE | 8 节点外推边界 | 🔬 🎓 |
| CL-JOS-CN | 中文文献与国内对比是否够 JOS 初审 | 🔬 ✍️ |
| CL-JOS-NOV | 创新深度 vs 工程报告 | 🔬 🔍 🎓 |

## Issue ID 前缀（JOS 增量）

| 前缀 | 含义 |
|------|------|
| `DOMAIN-J*` | JOS 创新性/国内文献 |
| `METHOD-J*` | JOS 实验/形式化不足 |
| `EDIT-J*` | JOS 模板/摘要/图表 |
| `ETHICS-J*` | JOS 原创/一稿多投风险 |

| 前缀 | 角色 | 示例 |
|------|------|------|
| `METHOD-` | 🔍 | 基线未披露发射频率 |
| `DOMAIN-` | 🔬 | 相关工作遗漏 OTel 采样 |
| `STAT-` | 📊 | 表1 σ 数量级错误 |
| `EDIT-` | ✍️ | MD 写首期、TeX 写三期 |
| `ETHICS-` | 📐 | 基金占位未删 |

## Major Issue 模板

```markdown
### STAT-M1: 表1 全量 σ 误写
- **位置**: `latex/sections/zh/06_experiments.tex` Lxx
- **证据**: `phase3_latest.json` → `comparison.full_collect.log_volume_stdev` = 1
- **问题**: 正文写 ±1000，与 L0 差三个数量级
- **建议**: 改为 4388±1（条）
- **验收标准**: `grep ±1000 latex/` 无匹配
- **需同步文件**: `docs/v4-论文稿件.md`、`docs/验证结果_三期.md`
```

## 05-全面评审报告 目录

1. 元信息  2. 执行摘要  3. 预检（含 J1–J7 若 JOS）  4. 分角色审稿  5. 交互质询  
6. 综合问题清单（P0→P2）  7. 亮点  8. 修改路线图  9. 证据索引（L0 字段表）  
10. **附录：JOS 投稿外 checklist**（在线投稿、定稿、投稿声明等）  
11. **附录：文献归档**（`cited_papers_manifest.json` 摘要）

## 行动清单模板

```markdown
| ID | 优先级 | 负责人 | 状态 | 关联 | 描述 | 验收标准 | 需同步文件 |
| AP-001 | P0 | 作者 | [ ] | C3a | 修正表1 σ | grep ±1000 → 0 | 06_experiments.tex, v4-论文稿件.md |
```

## 执行摘要模板

```markdown
# p3 论文审核执行摘要
- **run_id**:
- **决定**: Minor Revision / Major Revision / …
- **评分**: 方法论 / 领域 / overall
- **P0 共 n 项**:
- **最优先 3 件事**:
- **亮点**:
- **完整报告**: reviews/{run_id}/05-全面评审报告.md
```

## 回归验证（多轮迭代）

改稿后再次审核时，参见 [回归验证.md](回归验证.md)。

## 技能包内全部文档

[README.md](README.md) · [SKILL.md](SKILL.md) · [config.md](config.md) · [审核细则.md](审核细则.md) · [参考文献归档细则.md](参考文献归档细则.md) · [软件学报投稿要点.md](软件学报投稿要点.md) · [设计方案.md](设计方案.md) · [角色定义手册.md](角色定义手册.md) · [已知问题清单.md](已知问题清单.md) · [论文领域要点.md](论文领域要点.md) · [改稿衔接.md](改稿衔接.md) · [回归验证.md](回归验证.md)
