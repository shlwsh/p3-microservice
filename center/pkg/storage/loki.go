// Package storage 实现 Loki 存储适配层。
//
// 通过 Loki Push API (/loki/api/v1/push) 将日志写入 Grafana Loki。
// 支持批量推送、标签管理、压缩传输、重试机制。
//
// Loki 数据模型：
// - 每条日志由 labels（索引）+ timestamp + line（内容）组成
// - labels 用于日志流的分类和查询
// - 本组件将服务名、日志级别等关键字段设为 labels
package storage

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strconv"
	"sync"
	"time"
)

// LokiConfig Loki 存储配置。
type LokiConfig struct {
	PushURL     string        // Loki Push API 地址
	QueryURL    string        // Loki Query API 地址
	TenantID    string        // 多租户 ID
	BatchSize   int           // 批量推送条目数
	BatchWaitMs int64         // 批量等待时间（毫秒）
	PushTimeout time.Duration // 推送超时
	MaxRetries  int           // 最大重试次数
}

// LokiStore Loki 存储适配器。
type LokiStore struct {
	config     LokiConfig
	client     *http.Client
	buffer     []LokiStreamEntry
	mu         sync.Mutex
	flushCh    chan struct{}
}

// NewLokiStore 创建 Loki 存储适配器。
func NewLokiStore(cfg LokiConfig) (*LokiStore, error) {
	return &LokiStore{
		config: cfg,
		client: &http.Client{
			Timeout: cfg.PushTimeout,
		},
		buffer:  make([]LokiStreamEntry, 0, cfg.BatchSize),
		flushCh: make(chan struct{}, 1),
	}, nil
}

// ============================================================
// Loki Push API 数据结构
// ============================================================

// LokiPushRequest 对应 Loki Push API 的请求体。
type LokiPushRequest struct {
	Streams []LokiStream `json:"streams"`
}

// LokiStream 一个日志流（由相同 labels 标识）。
type LokiStream struct {
	Stream map[string]string `json:"stream"` // 标签集
	Values [][]string        `json:"values"` // [[timestamp_ns, line], ...]
}

// LokiStreamEntry 内部缓存的日志条目。
type LokiStreamEntry struct {
	Labels    map[string]string
	Timestamp time.Time
	Line      string
}

// ============================================================
// 写入接口
// ============================================================

// Write 写入一条日志到 Loki（先缓存，达到阈值后批量推送）。
func (s *LokiStore) Write(labels map[string]string, timestamp time.Time, line string) {
	s.mu.Lock()
	s.buffer = append(s.buffer, LokiStreamEntry{
		Labels:    labels,
		Timestamp: timestamp,
		Line:      line,
	})
	shouldFlush := len(s.buffer) >= s.config.BatchSize
	s.mu.Unlock()

	if shouldFlush {
		select {
		case s.flushCh <- struct{}{}:
		default:
		}
	}
}

// WriteBatch 批量写入日志。
func (s *LokiStore) WriteBatch(entries []LokiStreamEntry) {
	s.mu.Lock()
	s.buffer = append(s.buffer, entries...)
	shouldFlush := len(s.buffer) >= s.config.BatchSize
	s.mu.Unlock()

	if shouldFlush {
		select {
		case s.flushCh <- struct{}{}:
		default:
		}
	}
}

// RunBatchPusher 启动批量推送循环。
func (s *LokiStore) RunBatchPusher(ctx context.Context) {
	batchWait := time.Duration(s.config.BatchWaitMs) * time.Millisecond
	ticker := time.NewTicker(batchWait)
	defer ticker.Stop()

	log.Printf("[Loki] 批量推送器启动, batch_size=%d, batch_wait=%v",
		s.config.BatchSize, batchWait)

	for {
		select {
		case <-ctx.Done():
			log.Println("[Loki] 批量推送器停止")
			return
		case <-s.flushCh:
			s.flush()
		case <-ticker.C:
			s.flush()
		}
	}
}

// Flush 立即刷新缓冲区（优雅关闭时调用）。
func (s *LokiStore) Flush() {
	s.flush()
}

func (s *LokiStore) flush() {
	s.mu.Lock()
	if len(s.buffer) == 0 {
		s.mu.Unlock()
		return
	}
	entries := s.buffer
	s.buffer = make([]LokiStreamEntry, 0, s.config.BatchSize)
	s.mu.Unlock()

	// 按 labels 分组构建 streams
	streams := s.buildStreams(entries)
	pushReq := &LokiPushRequest{Streams: streams}

	// 推送到 Loki
	if err := s.push(pushReq); err != nil {
		log.Printf("[Loki] 推送失败: %v (%d 条日志)", err, len(entries))
	} else {
		log.Printf("[Loki] 推送成功: %d 条日志, %d 个流", len(entries), len(streams))
	}
}

// buildStreams 将缓存条目按 labels 分组为 Loki streams。
func (s *LokiStore) buildStreams(entries []LokiStreamEntry) []LokiStream {
	streamMap := make(map[string]*LokiStream)

	for _, entry := range entries {
		key := labelsKey(entry.Labels)

		stream, ok := streamMap[key]
		if !ok {
			stream = &LokiStream{
				Stream: entry.Labels,
				Values: make([][]string, 0),
			}
			streamMap[key] = stream
		}

		// Loki 要求时间戳为纳秒字符串
		tsNano := strconv.FormatInt(entry.Timestamp.UnixNano(), 10)
		stream.Values = append(stream.Values, []string{tsNano, entry.Line})
	}

	streams := make([]LokiStream, 0, len(streamMap))
	for _, stream := range streamMap {
		streams = append(streams, *stream)
	}
	return streams
}

// push 将数据推送到 Loki Push API。
func (s *LokiStore) push(req *LokiPushRequest) error {
	data, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("序列化失败: %w", err)
	}

	// gzip 压缩
	var buf bytes.Buffer
	gzWriter := gzip.NewWriter(&buf)
	if _, err := gzWriter.Write(data); err != nil {
		return fmt.Errorf("压缩失败: %w", err)
	}
	gzWriter.Close()

	// 带重试的推送
	var lastErr error
	for attempt := 0; attempt <= s.config.MaxRetries; attempt++ {
		httpReq, err := http.NewRequest("POST", s.config.PushURL, bytes.NewReader(buf.Bytes()))
		if err != nil {
			return fmt.Errorf("创建请求失败: %w", err)
		}

		httpReq.Header.Set("Content-Type", "application/json")
		httpReq.Header.Set("Content-Encoding", "gzip")
		if s.config.TenantID != "" {
			httpReq.Header.Set("X-Scope-OrgID", s.config.TenantID)
		}

		resp, err := s.client.Do(httpReq)
		if err != nil {
			lastErr = fmt.Errorf("HTTP 请求失败: %w", err)
			time.Sleep(time.Duration(attempt+1) * 200 * time.Millisecond)
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		if resp.StatusCode == http.StatusNoContent || resp.StatusCode == http.StatusOK {
			return nil // 成功
		}

		lastErr = fmt.Errorf("Loki 返回 %d: %s", resp.StatusCode, string(body))

		// 4xx 错误不重试（客户端错误）
		if resp.StatusCode >= 400 && resp.StatusCode < 500 {
			return lastErr
		}

		time.Sleep(time.Duration(attempt+1) * 200 * time.Millisecond)
	}

	return lastErr
}

// labelsKey 将 labels map 转为稳定的字符串键。
func labelsKey(labels map[string]string) string {
	// 简单实现：直接 JSON 序列化（生产环境应排序后拼接）
	data, _ := json.Marshal(labels)
	return string(data)
}
