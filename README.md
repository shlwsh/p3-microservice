# 分布式定向日志采集组件

> Distributed Directed Log Collector for Microservice Architecture

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

## 架构

```
网关节点 → 中心规则控制器 → 关注清单生成与下发 → 微服务节点匹配与采集
    → 固定缓存 + 指数退避上传 → 中心二次过滤 → Loki 存储
```

## 快速启动

```bash
# WSL 一键启动（推荐）
./deploy/wsl/setup.sh start

# 或手动启动
cd deploy/docker
docker compose -f docker-compose.yml -f docker-compose.wsl.yml up -d --build

# 健康检查
./deploy/wsl/verify.sh

# 访问
# Grafana:  http://localhost:3000 (admin/admin)
# Gateway:  http://localhost:8088/health
# Center:   http://localhost:8080/api/v1/health
# Loki:     http://localhost:3100/ready
```

## 文档

- [设计方案](docs/v1-设计方案.md)
- [实现方案](docs/v2-实现方案.md)

## 技术栈

- **Go 1.22** — Agent + Center 全栈
- **gRPC + Protobuf** — 高性能通信
- **Grafana Loki** — 日志存储
- **Redis** — 高速缓存
- **OpenResty + Lua** — 网关流量采集
- **Docker + Kubernetes** — 容器化部署
