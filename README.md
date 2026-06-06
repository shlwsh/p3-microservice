# 分布式定向日志采集组件

> Distributed Directed Log Collector for Microservice Architecture  
> 投稿目标：《计算机学报》

[![Go](https://img.shields.io/badge/Go-1.22-blue.svg)](https://go.dev/)
[![Loki](https://img.shields.io/badge/Loki-2.9-orange.svg)](https://grafana.com/oss/loki/)
[![gRPC](https://img.shields.io/badge/gRPC-1.64-green.svg)](https://grpc.io/)

## 概述

针对微服务分布式系统中日志分散、格式异构、海量数据导致的资源消耗高、实时性差和运维复杂等问题，本项目实现了一种**分布式定向日志采集组件**。

核心创新：
- **动态定向策略** — 基于网关流量日志驱动的关注清单生成，实现"只采必要日志"
- **固定缓存块算法** — 环形队列 + 资源感知的异步传输
- **定向策略三次转换** — 从流量监控到精细化日志过滤的完整链路
- **指数退避重试** — 压力感知的可靠传输机制

## 项目结构

```
p3-microservice/
├── docs/              # 设计文档、科研计划、论文初稿
├── experiments/       # 实验配置、脚本、结果（L0）
├── figures/           # 论文图表（图1–6）
├── latex/             # LaTeX 源稿
├── scripts/           # 科研/部署流水线
├── agent/ center/     # Go 工程代码
└── deploy/            # Docker / WSL 部署
```

## 快速启动（部署）

```bash
./deploy/wsl/setup.sh start    # 启动集群
./deploy/wsl/verify.sh         # 健康检查
```

详见 [部署说明](docs/部署说明.md)。

## 论文编译

| 版本 | 命令 | 产出 |
|------|------|------|
| 计算机学报体例（ctexart 近似） | `./scripts/build_pdf.sh` | `latex/main-zh.pdf` |
| **软件学报体例（rjthesis）** | `./scripts/build_pdf_jos.sh` | `docs/v4-论文稿件-jos.pdf` |
| 期刊模板库（含计算机学报官方 + Overleaf 版） | `./scripts/update_latex_models.sh` | `docs/latex-models/` |

模板说明见 [docs/latex-models/README.md](docs/latex-models/README.md)。

## 科研工作流

```bash
# 首期：架构图 + 算法微基准
bash scripts/p3_run_phase1.sh

# 二期：gRPC 全链路实测 + 定向 vs 全量对比
bash scripts/p3_run_phase2.sh
```

产出：
- `experiments/results/phase1/phase1_latest.json` — 实验数据
- `figures/fig1_*.pdf` … `fig6_*.pdf` — 论文图表
- `docs/验证结果_首期.md` — 结果摘要

## 文档索引

| 文档 | 说明 |
|------|------|
| [科研计划](docs/科研计划.md) | 阶段规划、贡献、行动清单 |
| [实验方案](docs/v3-实验方案.md) | E1–E4 对比、A1–A4 消融 |
| [论文初稿](docs/v4-论文稿件.md) | 《计算机学报》首期稿件 |
| [验证结果（首期）](docs/验证结果_首期.md) | 自动生成实验摘要 |
| [部署说明](docs/部署说明.md) | WSL 环境配置与运维 |
| [设计方案](docs/v1-设计方案.md) | 论文级系统设计 |
| [实现方案](docs/v2-实现方案.md) | 技术选型与模块地图 |
| [学习手册](docs/study/README.md) | 论文全景与定位 |

## 访问地址（集群运行中）

| 服务 | 地址 |
|------|------|
| Gateway | http://localhost:8088/health |
| Center API | http://localhost:8080/api/v1/health |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100/ready |

## 技术栈

- **Go 1.22** — Agent + Center
- **gRPC + Protobuf** — 高性能通信
- **Grafana Loki** — 日志存储
- **Redis** — 高速缓存
- **OpenResty + Lua** — 网关流量采集
- **Docker Compose** — WSL 本地部署
