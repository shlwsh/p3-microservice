// Package strategy - 定向策略三次转换算法。
//
// 三次转换是本组件的核心创新，实现从定向策略到精细化日志过滤的完整链路：
//
// 第一次转换：策略 → 网关采集规则
//   输入：定向策略（超时阈值、错误码列表等）
//   输出：Nginx Lua 可执行的过滤条件
//   作用：控制网关节点采集哪些流量日志
//
// 第二次转换：网关日志 + 策略 → 关注清单 → 服务节点过滤规则
//   输入：网关流量日志 + 定向策略
//   输出：关注清单（URL 模式 + 权重）→ Agent 过滤规则
//   作用：驱动各微服务节点的定向日志采集
//
// 第三次转换：关注清单 + 服务日志 → 中心二次过滤与转存规则
//   输入：关注清单 + Agent 上传的服务日志
//   输出：最终入库条件（过滤、结构化后写入 Loki）
//   作用：Center 侧的最终质量把关
package strategy

import (
	"context"
	"log"
	"time"

	"github.com/p3-microservice/center/pkg/dispatch"
	"github.com/p3-microservice/center/pkg/receiver"
	"github.com/p3-microservice/center/pkg/redisstore"
)

// TripleTransformConfig 三次转换配置。
type TripleTransformConfig struct {
	ListGenerator *AttentionListGenerator
	Dispatcher    *dispatch.RuleDispatcher
	Receiver      *receiver.LogReceiver
	GatewayStore  *redisstore.GatewayLogStore
	TimeWindowSec int64
	Strategy      *DirectedStrategy
}

// TripleTransformer 三次转换引擎。
type TripleTransformer struct {
	config TripleTransformConfig
}

// NewTripleTransformer 创建三次转换引擎。
func NewTripleTransformer(cfg TripleTransformConfig) *TripleTransformer {
	return &TripleTransformer{
		config: cfg,
	}
}

// ========================================
// 第一次转换：策略 → 网关采集规则
// ========================================

// GatewayCollectionRule 网关采集规则（Nginx Lua 可执行）。
type GatewayCollectionRule struct {
	// 采集条件
	MinResponseTimeMs int64  `json:"min_response_time_ms"` // 最小响应时间（低于此值不采集）
	CollectErrorCodes []int  `json:"collect_error_codes"`   // 需要采集的状态码
	SamplingRate      float64 `json:"sampling_rate"`        // 非异常请求采样率 (0.0-1.0)
	// 采集字段
	CollectFields []string `json:"collect_fields"`        // 需要采集的字段列表
}

// FirstTransform 执行第一次转换：策略 → 网关采集规则。
//
// 将抽象的定向策略转化为 Nginx Lua 脚本可直接使用的采集条件。
// 例如：超时阈值 1000ms → 网关仅采集响应时间 > 200ms 的请求（预筛选），
// 同时对正常请求按 10% 采样以保留基线数据。
func (t *TripleTransformer) FirstTransform(strategy *DirectedStrategy) *GatewayCollectionRule {
	// 网关预筛选阈值设为策略阈值的 20%（捕获潜在异常的上升趋势）
	preFilterThreshold := strategy.ResponseTimeThresholdMs / 5
	if preFilterThreshold < 50 {
		preFilterThreshold = 50 // 最低 50ms
	}

	rule := &GatewayCollectionRule{
		MinResponseTimeMs: preFilterThreshold,
		CollectErrorCodes: strategy.ErrorCodes,
		SamplingRate:      0.1, // 正常请求 10% 采样
		CollectFields: []string{
			"url", "method", "status_code", "response_time_ms",
			"client_ip", "request_size", "response_size",
			"upstream_addr", "timestamp",
		},
	}

	log.Printf("[Transform-1] 策略 → 网关规则: threshold=%dms, error_codes=%v, sampling=%.1f%%",
		rule.MinResponseTimeMs, rule.CollectErrorCodes, rule.SamplingRate*100)

	return rule
}

// ========================================
// 第二次转换：网关日志 → 关注清单 → Agent 过滤规则
// ========================================

// AgentFilterRule Agent 节点过滤规则。
type AgentFilterRule struct {
	Version    string              `json:"version"`
	Items      []AttentionListItem `json:"items"`
	MinLevel   string              `json:"min_level"`   // 最低日志级别
	ExpiresAt  time.Time           `json:"expires_at"`
}

// SecondTransform 执行第二次转换：网关日志 → 关注清单 → Agent 过滤规则。
//
// 1. 调用 AttentionListGenerator 分析网关流量日志
// 2. 生成关注清单
// 3. 转化为各 Agent 可执行的过滤规则
// 4. 通过 RuleDispatcher 下发至所有 Agent
func (t *TripleTransformer) SecondTransform(gatewayLogs []GatewayLog) *AgentFilterRule {
	// 生成关注清单
	list := t.config.ListGenerator.Generate(gatewayLogs)

	// 转化为 Agent 过滤规则
	rule := &AgentFilterRule{
		Version:   list.Version,
		Items:     list.Items,
		MinLevel:  "WARN", // 默认只采集 WARN 及以上（ERROR/FATAL 始终采集）
		ExpiresAt: list.ExpiresAt,
	}

	// 如果有高权重异常模式，降低日志级别到 INFO 以采集更多上下文
	for _, item := range list.Items {
		if item.Weight > 0.8 {
			rule.MinLevel = "INFO"
			break
		}
	}

	log.Printf("[Transform-2] 网关日志 → Agent 规则: version=%s, items=%d, min_level=%s",
		rule.Version, len(rule.Items), rule.MinLevel)

	// 下发规则到所有 Agent
	if t.config.Dispatcher != nil {
		t.config.Dispatcher.BroadcastRules(rule)
	}

	return rule
}

// ========================================
// 第三次转换：服务日志 → 存储规则
// ========================================

// ThirdTransform 执行第三次转换：关注清单 + 服务日志 → 存储规则。
//
// Center 接收到 Agent 上传的日志后，执行二次过滤：
// 1. 验证日志是否仍在当前关注清单内（清单可能已更新）
// 2. 去重（同一 TraceID 的日志只保留一次）
// 3. 结构化转换（提取关键字段为 Loki labels）
// 4. 写入 Loki
func (t *TripleTransformer) ThirdTransform(currentList *AttentionList) *receiver.StorageRule {
	rule := &receiver.StorageRule{
		Labels: map[string]string{
			"job":     "directed-log-collector",
			"version": currentList.Version,
		},
		KeepRawContent: true,
		ExtractFields: []string{
			"service_name", "url", "status_code", "response_time_ms",
			"trace_id", "level",
		},
		DedupWindowSec: 60,
	}

	log.Printf("[Transform-3] 关注清单 → 存储规则: labels=%v, dedup=%ds",
		rule.Labels, rule.DedupWindowSec)

	// 更新 LogReceiver 的过滤规则
	if t.config.Receiver != nil {
		t.config.Receiver.UpdateStorageRule(rule)
	}

	return rule
}

// ========================================
// 周期性生成
// ========================================

// RunPeriodicGeneration 启动周期性的三次转换流程。
//
// 每个周期执行：
// 1. 从 Redis 读取最近时间窗口的网关流量日志
// 2. 执行第二次转换（含关注清单生成）
// 3. 执行第三次转换（更新存储规则）
func (t *TripleTransformer) RunPeriodicGeneration(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	log.Printf("[TripleTransform] 周期性生成启动, interval=%v", interval)

	for {
		select {
		case <-ctx.Done():
			log.Println("[TripleTransform] 周期性生成停止")
			return
		case <-ticker.C:
			t.executeOneRound()
		}
	}
}

func (t *TripleTransformer) executeOneRound() {
	log.Println("[TripleTransform] ========== 开始新一轮转换 ==========")

	var gatewayLogs []GatewayLog
	if t.config.GatewayStore != nil {
		window := t.config.TimeWindowSec
		if window <= 0 {
			window = 60
		}
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		logs, err := t.config.GatewayStore.FetchWindow(ctx, window)
		cancel()
		if err != nil {
			log.Printf("[TripleTransform] 读取 Redis 网关日志失败: %v", err)
			return
		}
		gatewayLogs = logs
	}

	if len(gatewayLogs) == 0 {
		log.Println("[TripleTransform] 无网关流量日志，跳过本轮")
		return
	}
	log.Printf("[TripleTransform] 读取网关流量日志 %d 条", len(gatewayLogs))

	// 第二次转换
	t.SecondTransform(gatewayLogs)

	// 第三次转换
	currentList := t.config.ListGenerator.GetCurrentList()
	t.ThirdTransform(currentList)

	log.Println("[TripleTransform] ========== 本轮转换完成 ==========")
}

// ========================================
// 定向策略数据结构
// ========================================

// DirectedStrategy 定向策略。
type DirectedStrategy struct {
	StrategyID              string  `json:"strategy_id"`
	Name                    string  `json:"name"`
	ResponseTimeThresholdMs int64   `json:"response_time_threshold_ms"`
	ErrorCodes              []int   `json:"error_codes"`
	ErrorRateThreshold      float64 `json:"error_rate_threshold"`
	TimeWindowSec           int64   `json:"time_window_sec"`
	Enabled                 bool    `json:"enabled"`
}
