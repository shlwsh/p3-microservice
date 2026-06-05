// Package grpcserver 实现 Center 的 gRPC 服务端。
//
// 对外提供：
// 1. UploadLogBatch - 接收 Agent 批量上传的日志
// 2. PullAttentionList - Agent 拉取关注清单
// 3. Heartbeat - Agent 心跳上报
package grpcserver

import (
	"context"
	"log"

	"github.com/p3-microservice/center/pkg/dispatch"
	"github.com/p3-microservice/center/pkg/receiver"
	"github.com/p3-microservice/center/pkg/strategy"

	"google.golang.org/grpc"
)

// Config gRPC 服务配置。
type Config struct {
	LogReceiver *receiver.LogReceiver
	Dispatcher  *dispatch.RuleDispatcher
	ListGen     *strategy.AttentionListGenerator
}

// Server gRPC 服务端。
type Server struct {
	config Config
}

// NewServer 创建 gRPC 服务端。
func NewServer(cfg Config) *Server {
	return &Server{
		config: cfg,
	}
}

// Register 注册 gRPC 服务到 grpc.Server。
func (s *Server) Register(srv *grpc.Server) {
	// TODO: 当 proto 生成代码完成后，注册实际的 gRPC 服务
	// logpb.RegisterLogUploadServiceServer(srv, s)
	log.Println("[gRPC] 服务注册完成")
}

// UploadLogBatch 接收 Agent 批量上传的日志。
//
// 处理流程：
// 1. 解析请求（支持压缩和非压缩）
// 2. 幂等检查（基于 batchId 去重）
// 3. 转发给 LogReceiver 处理
func (s *Server) UploadLogBatch(ctx context.Context, agentID string, batchID string, entries []receiver.ReceivedLogEntry) (int, error) {
	log.Printf("[gRPC] UploadLogBatch: agent=%s, batch=%s, count=%d",
		agentID, batchID, len(entries))

	// TODO: 幂等检查（Redis SETNX batchId）

	stored, err := s.config.LogReceiver.ReceiveBatch(entries)
	if err != nil {
		return 0, err
	}

	return stored, nil
}

// PullAttentionList Agent 拉取关注清单。
//
// 返回当前最新的关注清单。支持增量更新（基于 currentVersion 对比）。
func (s *Server) PullAttentionList(ctx context.Context, agentID string, currentVersion string) (*strategy.AttentionList, bool) {
	currentList := s.config.ListGen.GetCurrentList()
	if currentList == nil {
		return nil, false
	}

	// 版本相同则不需要更新
	if currentList.Version == currentVersion {
		return nil, false
	}

	log.Printf("[gRPC] PullAttentionList: agent=%s, old_ver=%s, new_ver=%s",
		agentID, currentVersion, currentList.Version)

	return currentList, true
}

// Heartbeat 处理 Agent 心跳。
func (s *Server) Heartbeat(ctx context.Context, agentID string, cpuUsage, memUsage float64) (bool, bool) {
	// 注册/更新 Agent
	s.config.Dispatcher.RegisterAgent(agentID, &dispatch.AgentInfo{
		AgentID:    agentID,
		CPUUsage:   cpuUsage,
		MemoryUsage: memUsage,
	})

	needUpdate := s.config.Dispatcher.Heartbeat(agentID, cpuUsage, memUsage)
	forceFlush := false // 可根据策略动态决定

	return needUpdate, forceFlush
}
