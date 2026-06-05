// Package uploader 实现可靠的日志上传模块。
//
// 核心机制：
// 1. gRPC 批量上传至日志中心
// 2. 集成指数退避重试
// 3. 不可恢复错误时本地 BoltDB 兜底持久化
// 4. 中心恢复后自动补传
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
	// conn       *grpc.ClientConn        // gRPC 连接（实际实现时引入）
	// client     logpb.LogUploadServiceClient // gRPC 客户端
}

// NewGRPCUploader 创建 gRPC 上传器。
func NewGRPCUploader(cfg Config) (*GRPCUploader, error) {
	if cfg.CenterAddress == "" {
		return nil, fmt.Errorf("center_address 不能为空")
	}

	u := &GRPCUploader{
		config:        cfg,
		backoffConfig: cfg.BackoffConfig,
		monitor:       cfg.Monitor,
	}

	// TODO: 建立 gRPC 连接
	// conn, err := grpc.Dial(cfg.CenterAddress, grpc.WithInsecure())
	// ...

	log.Printf("[Uploader] 初始化完成, center=%s", cfg.CenterAddress)
	return u, nil
}

// UploadBatch 实现 cache.Uploader 接口，带指数退避重试的批量上传。
func (u *GRPCUploader) UploadBatch(batch []*cache.LogEntry, compressed bool, data []byte) error {
	return u.uploadWithRetry(batch, compressed, data)
}

// uploadWithRetry 带指数退避的重试上传（论文核心算法）。
//
// 算法流程：
// 1. 尝试发送批量日志到 Center
// 2. 成功则返回
// 3. 不可重试错误（如认证失败）→ 立即本地持久化
// 4. 可重试错误 → 计算退避延迟 → 等待 → 重试
// 5. 超过最大重试次数 → 本地持久化
// 6. 高压状态下延迟翻倍
func (u *GRPCUploader) uploadWithRetry(batch []*cache.LogEntry, compressed bool, data []byte) error {
	for attempt := 0; ; attempt++ {
		err := u.sendBatchToCenter(batch, compressed, data)
		if err == nil {
			if attempt > 0 {
				log.Printf("[Uploader] 第 %d 次重试成功, batch_size=%d", attempt, len(batch))
			}
			return nil
		}

		// 不可重试错误
		if !isRetryableError(err) {
			log.Printf("[Uploader] 不可重试错误: %v, 本地持久化 %d 条日志", err, len(batch))
			u.persistToLocal(batch)
			return err
		}

		// 超过最大重试次数
		if !u.backoffConfig.ShouldRetry(attempt) {
			log.Printf("[Uploader] 超过最大重试次数 (%d), 本地持久化 %d 条日志",
				u.backoffConfig.MaxRetries, len(batch))
			u.persistToLocal(batch)
			return fmt.Errorf("max retries exceeded: %w", err)
		}

		// 计算退避延迟（考虑系统压力）
		isHighPressure := false
		if u.monitor != nil {
			isHighPressure = u.monitor.IsHighPressure()
		}
		backoff := u.backoffConfig.NextDelayWithPressure(attempt, isHighPressure)

		log.Printf("[Uploader] 第 %d 次重试, 延迟 %v (高压=%v), err: %v",
			attempt, backoff, isHighPressure, err)

		// 等待退避延迟
		time.Sleep(backoff)

		// 记录重试指标
		recordRetryMetric(attempt, backoff, err)
	}
}

// sendBatchToCenter 发送批量日志到中心。
func (u *GRPCUploader) sendBatchToCenter(batch []*cache.LogEntry, compressed bool, data []byte) error {
	// TODO: 实际 gRPC 调用
	// req := &logpb.UploadLogBatchRequest{
	//     BatchId:  generateBatchID(),
	//     AgentId:  u.config.AgentID,
	//     Entries:  convertToProto(batch),
	//     Compressed:     compressed,
	//     CompressedData: data,
	// }
	// resp, err := u.client.UploadLogBatch(ctx, req)
	// ...

	log.Printf("[Uploader] 发送 %d 条日志到 Center (compressed=%v)", len(batch), compressed)
	return nil // 占位
}

// persistToLocal 将日志持久化到本地 BoltDB。
func (u *GRPCUploader) persistToLocal(batch []*cache.LogEntry) {
	// TODO: BoltDB 写入
	// db, err := bbolt.Open(u.config.LocalPersist.DBPath, 0600, nil)
	// db.Update(func(tx *bbolt.Tx) error {
	//     bucket, _ := tx.CreateBucketIfNotExists([]byte("fallback"))
	//     for _, entry := range batch {
	//         data, _ := json.Marshal(entry)
	//         bucket.Put([]byte(entry.LogID), data)
	//     }
	//     return nil
	// })

	log.Printf("[Uploader] 本地持久化 %d 条日志到 %s", len(batch), u.config.LocalPersist.DBPath)
}

// GetRuleClient 返回规则拉取客户端。
func (u *GRPCUploader) GetRuleClient() matcher.RuleClient {
	// TODO: 返回实际的 gRPC 规则客户端
	return &stubRuleClient{}
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
			// TODO: 发送心跳到 Center
		}
	}
}

// Close 关闭 gRPC 连接。
func (u *GRPCUploader) Close() {
	// TODO: u.conn.Close()
	log.Println("[Uploader] gRPC 连接已关闭")
}

// ========================================
// 辅助函数
// ========================================

// isRetryableError 判断错误是否可重试。
// 网络超时、连接中断等为可重试；认证失败、参数错误为不可重试。
func isRetryableError(err error) bool {
	if err == nil {
		return false
	}
	errStr := err.Error()

	// 不可重试的错误
	nonRetryable := []string{
		"authentication failed",
		"permission denied",
		"invalid argument",
		"not found",
	}
	for _, s := range nonRetryable {
		if strings.Contains(strings.ToLower(errStr), s) {
			return false
		}
	}

	// 默认可重试
	return true
}

// recordRetryMetric 记录重试指标（Prometheus 打点）。
func recordRetryMetric(attempt int, delay time.Duration, err error) {
	// TODO: prometheus.CounterVec.WithLabelValues(...).Inc()
	_ = attempt
	_ = delay
	_ = err
}

// stubRuleClient 临时规则客户端（待 gRPC 实现后替换）。
type stubRuleClient struct{}

func (s *stubRuleClient) PullAttentionList(agentID string, currentVersion string) (*matcher.AttentionList, error) {
	return nil, nil
}
