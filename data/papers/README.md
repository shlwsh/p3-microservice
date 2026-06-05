# 参考文献 PDF 归档

> 由 `scholar-search` 技能检索并下载。索引见 `papers_index.json`。

## 已下载（开放获取 / arXiv）

| 文件 | DOI | 与本文关联 |
|------|-----|-----------|
| `2023_Zhang_Robust_Failure_Diagnosis_...pdf` | 10.48550/arXiv.2302.10512 | 微服务多模态（日志+追踪）故障诊断 |
| `2024_Wang_A_Comprehensive_Survey_on_Root_Cause_...pdf` | 10.48550/arXiv.2408.00803 | 微服务根因分析综述 |
| `2024_Zhang_Failure_Diagnosis_in_Microservice_Systems.pdf` | 10.48550/arXiv.2407.01710 | 微服务故障诊断综述 |
| `2022_Maruf_Using_Microservice_Telemetry_Data_...pdf` | 10.48550/arXiv.2207.02776 | 微服务遥测（含日志）动态分析 |
| `2022_Vale_Designing_Microservice_Systems_Using_Patterns_...pdf` | 10.48550/arXiv.2201.03598 | 微服务模式与质量权衡 |
| `2023_Cheng_AI_for_IT_Operations_AIOps_...pdf` | 10.48550/arXiv.2304.04661 | 云原生 AIOps 与运维可观测性 |
| `2023_Xie_PBScaler_...pdf` | 10.48550/arXiv.2303.14620 | 微服务性能瓶颈（辅助背景） |
| `2022_Xu_A_Full_Dive_into_Realizing_the_Edge-enabled_Metave.pdf` | 10.48550/arXiv.2203.05471 | 边缘计算背景（弱相关，可替换） |

## 已录入 DOI、待机构订阅获取 PDF

见 `data/scholar/curated.json`：`li2021observability`、`burns2016patterns`、`jamshidi2018microservices`、`soldani2024logs`、`zhu2023sidecar`、`varghese2022edge` 等。

## 复现下载

```bash
python .agent/skills/scholar-search/scripts/scholar_search.py \
  --query "microservice log observability" --backend openalex --arxiv-only --num 15 \
  --output data/scholar/results_arxiv.json

python .agent/skills/scholar-search/scripts/download_papers.py \
  --input data/scholar/curated.json --output-dir data/papers --max-downloads 12
```
