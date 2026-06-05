// Package receiver 实现日志接收与二次过滤。
//
// Center 侧接收 Agent 上传的日志后，执行二次过滤：
// 1. 验证日志是否匹配当前关注清单
// 2. 基于 TraceID 去重
// 3. 结构化转换（提取 Loki labels）
// 4. 写入 Loki
package receiver

import (
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/p3-microservice/center/pkg/storage"
)

// Config 日志接收器配置。
type Config struct {
	Store           *storage.LokiStore
	SecondaryFilter bool  // 是否启用二次过滤
	DedupWindowSec  int64 // 去重窗口（秒）
}

// ReceivedLogEntry 接收到的日志条目。
type ReceivedLogEntry struct {
	LogID          string            `json:"log_id"`
	ServiceName    string            `json:"service_name"`
	InstanceID     string            `json:"instance_id"`
	Timestamp      time.Time         `json:"timestamp"`
	Level          string            `json:"level"`
	URL            string            `json:"url"`
	Method         string            `json:"method"`
	StatusCode     int               `json:"status_code"`
	ResponseTimeMs int64             `json:"response_time_ms"`
	TraceID        string            `json:"trace_id"`
	SpanID         string            `json:"span_id"`
	Content        string            `json:"content"`
	ClientIP       string            `json:"client_ip"`
	Source         string            `json:"source"`
	Metadata       map[string]string `json:"metadata"`
}

// StorageRule 存储规则（由三次转换的第三步生成）。
type StorageRule struct {
	Labels         map[string]string `json:"labels"`
	KeepRawContent bool              `json:"keep_raw_content"`
	ExtractFields  []string          `json:"extract_fields"`
	DedupWindowSec int64             `json:"dedup_window_sec"`
}

// LogReceiver 日志接收与二次过滤器。
type LogReceiver struct {
	config      Config
	store       *storage.LokiStore
	storageRule *StorageRule
	ruleMu      sync.RWMutex

	// 去重缓存（TraceID → 最后见到的时间）
	dedupCache map[string]time.Time
	dedupMu    sync.Mutex

	// 统计
	receivedCount  int64
	filteredCount  int64
	dedupCount     int64
	storedCount    int64
}

// NewLogReceiver 创建日志接收器。
func NewLogReceiver(cfg Config) *LogReceiver {
	return &LogReceiver{
		config:     cfg,
		store:      cfg.Store,
		dedupCache: make(map[string]time.Time),
		storageRule: &StorageRule{
			Labels: map[string]string{
				"job": "directed-log-collector",
			},
			KeepRawContent: true,
			DedupWindowSec: cfg.DedupWindowSec,
		},
	}
}

// ReceiveBatch 接收一批日志条目并处理。
//
// 处理流程：
// 1. 二次过滤（若启用）
// 2. TraceID 去重
// 3. 结构化转换
// 4. 写入 Loki
func (r *LogReceiver) ReceiveBatch(entries []ReceivedLogEntry) (int, error) {
	r.receivedCount += int64(len(entries))

	var processed []storage.LokiStreamEntry

	for i := range entries {
		entry := &entries[i]

		// 二次过滤
		if r.config.SecondaryFilter {
			if !r.shouldKeep(entry) {
				r.filteredCount++
				continue
			}
		}

		// 去重
		if r.isDuplicate(entry) {
			r.dedupCount++
			continue
		}

		// 结构化转换 → Loki 条目
		lokiEntry := r.toLokiEntry(entry)
		processed = append(processed, lokiEntry)
	}

	if len(processed) == 0 {
		return 0, nil
	}

	// 写入 Loki
	r.store.WriteBatch(processed)
	r.storedCount += int64(len(processed))

	log.Printf("[Receiver] 处理完成: received=%d, filtered=%d, dedup=%d, stored=%d",
		len(entries), r.filteredCount, r.dedupCount, len(processed))

	return len(processed), nil
}

// shouldKeep 二次过滤：判断日志是否应保留。
func (r *LogReceiver) shouldKeep(entry *ReceivedLogEntry) bool {
	// ERROR/FATAL 级别始终保留
	if entry.Level == "ERROR" || entry.Level == "FATAL" {
		return true
	}

	// 有 URL 且状态码异常 → 保留
	if entry.StatusCode >= 400 {
		return true
	}

	// 慢请求 → 保留
	if entry.ResponseTimeMs > 500 {
		return true
	}

	// 其他情况：检查是否匹配当前存储规则
	// （简化实现：直接保留）
	return true
}

// isDuplicate 基于 TraceID 的去重检查。
func (r *LogReceiver) isDuplicate(entry *ReceivedLogEntry) bool {
	if entry.TraceID == "" {
		return false // 无 TraceID 不去重
	}

	r.dedupMu.Lock()
	defer r.dedupMu.Unlock()

	dedupWindow := time.Duration(r.config.DedupWindowSec) * time.Second

	// 检查是否在去重窗口内已见过
	if lastSeen, ok := r.dedupCache[entry.TraceID]; ok {
		if time.Since(lastSeen) < dedupWindow {
			return true // 重复
		}
	}

	// 记录
	r.dedupCache[entry.TraceID] = time.Now()

	// 定期清理过期条目（简化：超过 10000 条时清理）
	if len(r.dedupCache) > 10000 {
		r.cleanupDedupCache(dedupWindow)
	}

	return false
}

// cleanupDedupCache 清理过期的去重缓存。
func (r *LogReceiver) cleanupDedupCache(window time.Duration) {
	now := time.Now()
	for k, v := range r.dedupCache {
		if now.Sub(v) > window {
			delete(r.dedupCache, k)
		}
	}
}

// toLokiEntry 将日志条目转换为 Loki 流条目。
func (r *LogReceiver) toLokiEntry(entry *ReceivedLogEntry) storage.LokiStreamEntry {
	r.ruleMu.RLock()
	rule := r.storageRule
	r.ruleMu.RUnlock()

	// 构建 labels
	labels := make(map[string]string)
	// 复制存储规则中的基础标签
	for k, v := range rule.Labels {
		labels[k] = v
	}
	// 添加日志特有标签
	labels["service"] = entry.ServiceName
	labels["level"] = entry.Level
	labels["source"] = entry.Source
	if entry.InstanceID != "" {
		labels["instance"] = entry.InstanceID
	}

	// 构建日志行
	var line string
	if rule.KeepRawContent {
		// JSON 格式保留全部字段
		data, err := json.Marshal(entry)
		if err != nil {
			line = fmt.Sprintf("[%s] %s %s %d %dms - %s",
				entry.Level, entry.Method, entry.URL,
				entry.StatusCode, entry.ResponseTimeMs, entry.Content)
		} else {
			line = string(data)
		}
	} else {
		line = fmt.Sprintf("[%s] %s %s %d %dms - %s",
			entry.Level, entry.Method, entry.URL,
			entry.StatusCode, entry.ResponseTimeMs, entry.Content)
	}

	return storage.LokiStreamEntry{
		Labels:    labels,
		Timestamp: entry.Timestamp,
		Line:      line,
	}
}

// UpdateStorageRule 更新存储规则（由三次转换引擎调用）。
func (r *LogReceiver) UpdateStorageRule(rule *StorageRule) {
	r.ruleMu.Lock()
	defer r.ruleMu.Unlock()
	r.storageRule = rule
	log.Printf("[Receiver] 存储规则已更新: labels=%v", rule.Labels)
}

// Stats 返回统计信息。
func (r *LogReceiver) Stats() ReceiverStats {
	return ReceiverStats{
		ReceivedCount: r.receivedCount,
		FilteredCount: r.filteredCount,
		DedupCount:    r.dedupCount,
		StoredCount:   r.storedCount,
		DedupCacheSize: int64(len(r.dedupCache)),
	}
}

// ReceiverStats 接收器统计。
type ReceiverStats struct {
	ReceivedCount  int64 `json:"received_count"`
	FilteredCount  int64 `json:"filtered_count"`
	DedupCount     int64 `json:"dedup_count"`
	StoredCount    int64 `json:"stored_count"`
	DedupCacheSize int64 `json:"dedup_cache_size"`
}
