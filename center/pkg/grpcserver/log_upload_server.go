package grpcserver

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/p3-microservice/center/pkg/dispatch"
	"github.com/p3-microservice/center/pkg/receiver"
	"github.com/p3-microservice/center/pkg/redisstore"
	"github.com/p3-microservice/center/pkg/gatewaylog"
	"github.com/p3-microservice/proto/logpb"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
)

// LogUploadServer 实现 logpb.LogUploadServiceServer。
type LogUploadServer struct {
	logpb.UnimplementedLogUploadServiceServer
	config      Config
	gatewayStore *redisstore.GatewayLogStore
	seenBatches sync.Map // batch_id 幂等
}

// NewLogUploadServer 创建 gRPC 日志上传服务。
func NewLogUploadServer(cfg Config, gatewayStore *redisstore.GatewayLogStore) *LogUploadServer {
	return &LogUploadServer{config: cfg, gatewayStore: gatewayStore}
}

func (s *LogUploadServer) UploadLogBatch(ctx context.Context, req *logpb.UploadLogBatchRequest) (*logpb.UploadLogBatchResponse, error) {
	if req.GetBatchId() != "" {
		if _, loaded := s.seenBatches.LoadOrStore(req.GetBatchId(), true); loaded {
			return &logpb.UploadLogBatchResponse{
				Success:       true,
				Message:       "duplicate batch",
				AcceptedCount: 0,
			}, nil
		}
	}

	agentID := req.GetAgentId()
	var gatewayLogs []gatewaylog.GatewayLog
	var appEntries []receiver.ReceivedLogEntry

	for _, e := range req.GetEntries() {
		if e.GetSource() == logpb.LogSource_GATEWAY {
			gatewayLogs = append(gatewayLogs, protoToGatewayLog(e))
			continue
		}
		appEntries = append(appEntries, protoToReceivedEntry(e, agentID))
	}

	accepted := int32(0)

	if len(gatewayLogs) > 0 && s.gatewayStore != nil {
		if err := s.gatewayStore.AppendBatch(ctx, gatewayLogs); err != nil {
			return nil, status.Errorf(codes.Internal, "redis append: %v", err)
		}
		accepted += int32(len(gatewayLogs))
		log.Printf("[gRPC] 网关流量日志入库 Redis: agent=%s, count=%d", agentID, len(gatewayLogs))
	}

	if len(appEntries) > 0 {
		stored, err := s.config.LogReceiver.ReceiveBatch(appEntries)
		if err != nil {
			return nil, status.Errorf(codes.Internal, "receive batch: %v", err)
		}
		accepted += int32(stored)
	}

	return &logpb.UploadLogBatchResponse{
		Success:       true,
		Message:       "ok",
		AcceptedCount: accepted,
		RejectedCount: int32(len(req.GetEntries())) - accepted,
	}, nil
}

func (s *LogUploadServer) StreamUploadLog(stream logpb.LogUploadService_StreamUploadLogServer) error {
	var entries []*logpb.LogEntry
	for {
		entry, err := stream.Recv()
		if err != nil {
			break
		}
		entries = append(entries, entry)
	}
	resp, err := s.UploadLogBatch(stream.Context(), &logpb.UploadLogBatchRequest{Entries: entries})
	if err != nil {
		return err
	}
	return stream.SendAndClose(resp)
}

func (s *LogUploadServer) PullAttentionList(ctx context.Context, req *logpb.PullAttentionListRequest) (*logpb.PullAttentionListResponse, error) {
	list, updated := s.config.ListGen.GetCurrentList(), true
	if req.GetCurrentVersion() != "" && list != nil && list.Version == req.GetCurrentVersion() {
		return &logpb.PullAttentionListResponse{Version: list.Version, FullUpdate: false}, nil
	}
	if list == nil {
		return &logpb.PullAttentionListResponse{}, nil
	}
	items := make([]*logpb.AttentionListItem, 0, len(list.Items))
	for _, it := range list.Items {
		items = append(items, &logpb.AttentionListItem{
			Pattern:     it.Pattern,
			PatternType: patternTypeToProto(it.PatternType),
			Weight:      it.Weight,
			Reason:      it.Reason,
			Keywords:    it.Keywords,
			TtlSeconds:  it.TTLSeconds,
		})
	}
	return &logpb.PullAttentionListResponse{
		Version:    list.Version,
		Items:      items,
		ExpiresAt:  timestamppb.New(list.ExpiresAt),
		FullUpdate: updated,
	}, nil
}

func (s *LogUploadServer) Heartbeat(ctx context.Context, req *logpb.HeartbeatRequest) (*logpb.HeartbeatResponse, error) {
	st := req.GetStatus()
	cpu, mem := 0.0, 0.0
	if st != nil {
		cpu, mem = st.GetCpuUsage(), st.GetMemoryUsage()
	}
	needUpdate := false
	if s.config.Dispatcher != nil {
		s.config.Dispatcher.RegisterAgent(req.GetAgentId(), &dispatch.AgentInfo{
			AgentID:     req.GetAgentId(),
			CPUUsage:    cpu,
			MemoryUsage: mem,
		})
		needUpdate = s.config.Dispatcher.Heartbeat(req.GetAgentId(), cpu, mem)
	}
	return &logpb.HeartbeatResponse{
		Acknowledged: true,
		UpdateRules:  needUpdate,
	}, nil
}

func protoToGatewayLog(e *logpb.LogEntry) gatewaylog.GatewayLog {
	ts := time.Now().UnixMilli()
	if e.GetTimestamp() != nil {
		ts = e.GetTimestamp().AsTime().UnixMilli()
	}
	return gatewaylog.GatewayLog{
		URL:            e.GetUrl(),
		Method:         e.GetMethod(),
		StatusCode:     int(e.GetStatusCode()),
		ResponseTimeMs: e.GetResponseTimeMs(),
		ClientIP:       e.GetClientIp(),
		Timestamp:      ts,
		ServiceName:    e.GetServiceName(),
	}
}

func protoToReceivedEntry(e *logpb.LogEntry, agentID string) receiver.ReceivedLogEntry {
	ts := time.Now()
	if e.GetTimestamp() != nil {
		ts = e.GetTimestamp().AsTime()
	}
	return receiver.ReceivedLogEntry{
		LogID:          e.GetLogId(),
		ServiceName:    e.GetServiceName(),
		InstanceID:     firstNonEmpty(e.GetInstanceId(), agentID),
		Timestamp:      ts,
		Level:          logLevelToString(e.GetLevel()),
		URL:            e.GetUrl(),
		Method:         e.GetMethod(),
		StatusCode:     int(e.GetStatusCode()),
		ResponseTimeMs: e.GetResponseTimeMs(),
		TraceID:        e.GetTraceId(),
		SpanID:         e.GetSpanId(),
		Content:        e.GetContent(),
		ClientIP:       e.GetClientIp(),
		Source:         sourceToString(e.GetSource()),
		Metadata:       e.GetMetadata(),
	}
}

func patternTypeToProto(t string) logpb.PatternType {
	switch t {
	case "exact":
		return logpb.PatternType_EXACT
	case "prefix":
		return logpb.PatternType_PREFIX
	case "regex":
		return logpb.PatternType_REGEX
	case "wildcard":
		return logpb.PatternType_WILDCARD
	default:
		return logpb.PatternType_PREFIX
	}
}

func logLevelToString(l logpb.LogLevel) string {
	switch l {
	case logpb.LogLevel_DEBUG:
		return "DEBUG"
	case logpb.LogLevel_INFO:
		return "INFO"
	case logpb.LogLevel_WARN:
		return "WARN"
	case logpb.LogLevel_ERROR:
		return "ERROR"
	case logpb.LogLevel_FATAL:
		return "FATAL"
	default:
		return "INFO"
	}
}

func sourceToString(s logpb.LogSource) string {
	switch s {
	case logpb.LogSource_GATEWAY:
		return "GATEWAY"
	case logpb.LogSource_APPLICATION:
		return "APPLICATION"
	default:
		return "SYSTEM"
	}
}

func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}

func stringToLogLevel(level string) logpb.LogLevel {
	switch level {
	case "DEBUG":
		return logpb.LogLevel_DEBUG
	case "INFO":
		return logpb.LogLevel_INFO
	case "WARN":
		return logpb.LogLevel_WARN
	case "ERROR":
		return logpb.LogLevel_ERROR
	case "FATAL":
		return logpb.LogLevel_FATAL
	default:
		return logpb.LogLevel_INFO
	}
}

func stringToLogSource(source string) logpb.LogSource {
	switch source {
	case "GATEWAY":
		return logpb.LogSource_GATEWAY
	case "APPLICATION":
		return logpb.LogSource_APPLICATION
	default:
		return logpb.LogSource_SYSTEM
	}
}

// CacheEntryToProto 将 Agent 缓存条目转为 proto（供 agent 侧引用时复制）。
func CacheEntryToProto(e interface {
	GetLogID() string
}) *logpb.LogEntry {
	return nil
}

// FormatBatchID 生成批次 ID。
func FormatBatchID(agentID string) string {
	return fmt.Sprintf("%s-%d", agentID, time.Now().UnixNano())
}
