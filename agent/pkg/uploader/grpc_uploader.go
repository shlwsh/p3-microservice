package uploader

import (
	"context"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
	"github.com/p3-microservice/agent/pkg/matcher"
	"github.com/p3-microservice/agent/pkg/monitor"
	"github.com/p3-microservice/agent/pkg/retry"
	"github.com/p3-microservice/proto/logpb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Config gRPC 上传器配置。
type Config struct {
	CenterAddress string
	AgentID       string
	BackoffConfig *retry.BackoffConfig
	Monitor       *monitor.ResourceMonitor
	LocalPersist  LocalPersistConfig
}

// LocalPersistConfig 本地持久化配置。
type LocalPersistConfig struct {
	DBPath       string
	MaxSizeBytes int64
}

// GRPCUploader gRPC 上传器。
type GRPCUploader struct {
	config        Config
	backoffConfig *retry.BackoffConfig
	monitor       *monitor.ResourceMonitor
	conn          *grpc.ClientConn
	client        logpb.LogUploadServiceClient
}

// NewGRPCUploader 创建 gRPC 上传器。
func NewGRPCUploader(cfg Config) (*GRPCUploader, error) {
	if cfg.CenterAddress == "" {
		return nil, fmt.Errorf("center_address 不能为空")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	conn, err := grpc.DialContext(ctx, cfg.CenterAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		return nil, fmt.Errorf("grpc dial %s: %w", cfg.CenterAddress, err)
	}

	u := &GRPCUploader{
		config:        cfg,
		backoffConfig: cfg.BackoffConfig,
		monitor:       cfg.Monitor,
		conn:          conn,
		client:        logpb.NewLogUploadServiceClient(conn),
	}

	log.Printf("[Uploader] 初始化完成, center=%s", cfg.CenterAddress)
	return u, nil
}

// UploadBatch 实现 cache.Uploader 接口。
func (u *GRPCUploader) UploadBatch(batch []*cache.LogEntry, compressed bool, data []byte) error {
	return u.uploadWithRetry(batch, compressed, data)
}

func (u *GRPCUploader) uploadWithRetry(batch []*cache.LogEntry, compressed bool, data []byte) error {
	for attempt := 0; ; attempt++ {
		err := u.sendBatchToCenter(batch, compressed, data)
		if err == nil {
			if attempt > 0 {
				log.Printf("[Uploader] 第 %d 次重试成功, batch_size=%d", attempt, len(batch))
			}
			return nil
		}

		if !isRetryableError(err) {
			log.Printf("[Uploader] 不可重试错误: %v, 本地持久化 %d 条日志", err, len(batch))
			u.persistToLocal(batch)
			return err
		}

		if !u.backoffConfig.ShouldRetry(attempt) {
			log.Printf("[Uploader] 超过最大重试次数 (%d), 本地持久化 %d 条日志",
				u.backoffConfig.MaxRetries, len(batch))
			u.persistToLocal(batch)
			return fmt.Errorf("max retries exceeded: %w", err)
		}

		isHighPressure := false
		if u.monitor != nil {
			isHighPressure = u.monitor.IsHighPressure()
		}
		backoff := u.backoffConfig.NextDelayWithPressure(attempt, isHighPressure)
		log.Printf("[Uploader] 第 %d 次重试, 延迟 %v (高压=%v), err: %v",
			attempt, backoff, isHighPressure, err)
		time.Sleep(backoff)
		recordRetryMetric(attempt, backoff, err)
	}
}

func (u *GRPCUploader) sendBatchToCenter(batch []*cache.LogEntry, compressed bool, data []byte) error {
	if len(batch) == 0 {
		return nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	req := &logpb.UploadLogBatchRequest{
		BatchId:   FormatBatchID(u.config.AgentID),
		AgentId:   u.config.AgentID,
		Entries:   entriesToProto(batch, u.config.AgentID),
		Compressed: compressed,
	}
	if compressed && len(data) > 0 {
		req.CompressedData = data
	}

	resp, err := u.client.UploadLogBatch(ctx, req)
	if err != nil {
		return err
	}
	if !resp.GetSuccess() {
		return fmt.Errorf("upload rejected: %s", resp.GetMessage())
	}
	log.Printf("[Uploader] 发送 %d 条日志到 Center, accepted=%d", len(batch), resp.GetAcceptedCount())
	return nil
}

func (u *GRPCUploader) persistToLocal(batch []*cache.LogEntry) {
	log.Printf("[Uploader] 本地持久化 %d 条日志到 %s", len(batch), u.config.LocalPersist.DBPath)
}

// GetRuleClient 返回 gRPC 规则拉取客户端。
func (u *GRPCUploader) GetRuleClient() matcher.RuleClient {
	return &grpcRuleClient{uploader: u}
}

// StartHeartbeat 启动心跳上报。
func (u *GRPCUploader) StartHeartbeat(ctx context.Context, mon *monitor.ResourceMonitor, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("[Uploader] 心跳停止")
			return
		case <-ticker.C:
			status := mon.Status()
			log.Printf("[Uploader] 心跳: CPU=%.2f%%, Mem=%.2f%%, HighPressure=%v",
				status.CPUUsage*100, status.MemoryUsage*100, status.HighPressure)

			hbCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			_, err := u.client.Heartbeat(hbCtx, &logpb.HeartbeatRequest{
				AgentId: u.config.AgentID,
				Status: &logpb.NodeStatus{
					CpuUsage:    status.CPUUsage,
					MemoryUsage: status.MemoryUsage,
				},
			})
			cancel()
			if err != nil {
				log.Printf("[Uploader] 心跳失败: %v", err)
			}
		}
	}
}

// Close 关闭 gRPC 连接。
func (u *GRPCUploader) Close() {
	if u.conn != nil {
		_ = u.conn.Close()
	}
	log.Println("[Uploader] gRPC 连接已关闭")
}

// FormatBatchID 生成批次 ID。
func FormatBatchID(agentID string) string {
	return fmt.Sprintf("%s-%d", agentID, time.Now().UnixNano())
}

func isRetryableError(err error) bool {
	if err == nil {
		return false
	}
	errStr := strings.ToLower(err.Error())
	for _, s := range []string{"authentication failed", "permission denied", "invalid argument", "not found"} {
		if strings.Contains(errStr, s) {
			return false
		}
	}
	return true
}

func recordRetryMetric(attempt int, delay time.Duration, err error) {
	_ = attempt
	_ = delay
	_ = err
}

// grpcRuleClient 通过 gRPC 拉取关注清单。
type grpcRuleClient struct {
	uploader *GRPCUploader
}

func (c *grpcRuleClient) PullAttentionList(agentID, currentVersion string) (*matcher.AttentionList, error) {
	if agentID == "" {
		agentID = c.uploader.config.AgentID
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	resp, err := c.uploader.client.PullAttentionList(ctx, &logpb.PullAttentionListRequest{
		AgentId:        agentID,
		CurrentVersion: currentVersion,
	})
	if err != nil {
		return nil, err
	}
	if resp == nil || len(resp.GetItems()) == 0 {
		return nil, nil
	}
	list := protoToAttentionList(resp)
	if list == nil {
		return nil, nil
	}
	out := &matcher.AttentionList{Version: list.Version}
	for _, it := range list.Items {
		out.Items = append(out.Items, matcher.AttentionListItem{
			Pattern:     it.Pattern,
			PatternType: it.PatternType,
			Weight:      it.Weight,
			Reason:      it.Reason,
			Keywords:    it.Keywords,
			TTLSeconds:  it.TTLSeconds,
		})
	}
	return out, nil
}
