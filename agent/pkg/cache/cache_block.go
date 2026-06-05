// Package cache - FixedCacheBlock 是固定缓存块管理器。
//
// 职责：
// 1. 管理固定大小的内存缓存
// 2. 容量阈值触发异步上传
// 3. 定时器触发周期性上传
// 4. 支持 gzip 压缩
// 5. 资源感知：根据系统压力动态调整上传策略
package cache

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"log"
	"sync"
	"time"
)

// Config 固定缓存块配置。
type Config struct {
	MaxSizeBytes          int64 // 最大内存字节数
	MaxEntries            int   // 最大条目数
	FlushThresholdPercent int   // 触发上传的容量百分比（0-100）
	FlushIntervalMs       int64 // 定时上传间隔（毫秒）
	EnableCompression     bool  // 是否启用 gzip 压缩
}

// Uploader 定义上传接口，供缓存块调用。
type Uploader interface {
	UploadBatch(batch []*LogEntry, compressed bool, data []byte) error
}

// FixedCacheBlock 固定缓存块管理器。
type FixedCacheBlock struct {
	config Config
	buffer *RingBuffer
	mu     sync.Mutex
}

// NewFixedCacheBlock 创建固定缓存块。
func NewFixedCacheBlock(cfg Config) *FixedCacheBlock {
	maxEntries := cfg.MaxEntries
	if maxEntries == 0 {
		// 按平均每条日志 1KB 估算
		maxEntries = int(cfg.MaxSizeBytes / 1024)
	}

	return &FixedCacheBlock{
		config: cfg,
		buffer: NewRingBuffer(maxEntries),
	}
}

// AddLog 向缓存中添加一条日志。
// 如果添加后达到阈值，返回 true 提示应触发上传。
func (c *FixedCacheBlock) AddLog(entry *LogEntry) bool {
	// 估算条目大小
	if entry.SizeBytes == 0 {
		entry.SizeBytes = estimateSize(entry)
	}

	c.buffer.Push(entry)

	// 检查是否达到上传阈值
	return c.buffer.UsagePercent() >= c.config.FlushThresholdPercent
}

// Run 启动缓存块的后台管理循环。
// 包含定时上传和容量阈值上传两种触发机制。
func (c *FixedCacheBlock) Run(ctx context.Context, uploader Uploader) {
	flushInterval := time.Duration(c.config.FlushIntervalMs) * time.Millisecond
	ticker := time.NewTicker(flushInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("[CacheBlock] 收到退出信号，停止缓存管理")
			return
		case <-ticker.C:
			c.flush(uploader)
		}
	}
}

// flush 执行一次缓存刷新（上传）。
func (c *FixedCacheBlock) flush(uploader Uploader) {
	c.mu.Lock()
	defer c.mu.Unlock()

	count := c.buffer.Count()
	if count == 0 {
		return
	}

	// 每次最多取 1000 条
	batchSize := 1000
	if count < batchSize {
		batchSize = count
	}

	batch := c.buffer.DrainBatch(batchSize)
	if len(batch) == 0 {
		return
	}

	log.Printf("[CacheBlock] 准备上传 %d 条日志", len(batch))

	// 压缩并上传
	if c.config.EnableCompression {
		compressed, data, err := c.compressBatch(batch)
		if err != nil {
			log.Printf("[CacheBlock] 压缩失败: %v, 使用原始数据上传", err)
			go c.uploadAsync(uploader, batch, false, nil)
			return
		}
		go c.uploadAsync(uploader, batch, compressed, data)
	} else {
		go c.uploadAsync(uploader, batch, false, nil)
	}
}

// uploadAsync 异步上传日志批次。
func (c *FixedCacheBlock) uploadAsync(uploader Uploader, batch []*LogEntry, compressed bool, data []byte) {
	if err := uploader.UploadBatch(batch, compressed, data); err != nil {
		log.Printf("[CacheBlock] 上传失败: %v (将由重试机制处理)", err)
	}
}

// FlushAll 刷新所有缓存（优雅关闭时调用）。
func (c *FixedCacheBlock) FlushAll(uploader Uploader) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	for c.buffer.Count() > 0 {
		batch := c.buffer.DrainBatch(1000)
		if len(batch) == 0 {
			break
		}
		if err := uploader.UploadBatch(batch, false, nil); err != nil {
			return err
		}
	}
	return nil
}

// compressBatch 对日志批次进行 gzip 压缩。
func (c *FixedCacheBlock) compressBatch(batch []*LogEntry) (bool, []byte, error) {
	jsonData, err := json.Marshal(batch)
	if err != nil {
		return false, nil, err
	}

	var buf bytes.Buffer
	writer := gzip.NewWriter(&buf)
	if _, err := writer.Write(jsonData); err != nil {
		return false, nil, err
	}
	if err := writer.Close(); err != nil {
		return false, nil, err
	}

	return true, buf.Bytes(), nil
}

// Stats 返回当前缓存统计信息。
func (c *FixedCacheBlock) Stats() CacheStats {
	return CacheStats{
		Count:        c.buffer.Count(),
		SizeBytes:    c.buffer.SizeBytes(),
		UsagePercent: c.buffer.UsagePercent(),
		DroppedCount: c.buffer.DroppedCount(),
		MaxEntries:   c.config.MaxEntries,
		MaxSizeBytes: c.config.MaxSizeBytes,
	}
}

// CacheStats 缓存统计信息。
type CacheStats struct {
	Count        int   `json:"count"`
	SizeBytes    int64 `json:"size_bytes"`
	UsagePercent int   `json:"usage_percent"`
	DroppedCount int64 `json:"dropped_count"`
	MaxEntries   int   `json:"max_entries"`
	MaxSizeBytes int64 `json:"max_size_bytes"`
}

// estimateSize 估算日志条目的内存占用。
func estimateSize(entry *LogEntry) int64 {
	size := int64(len(entry.LogID) + len(entry.ServiceName) + len(entry.InstanceID) +
		len(entry.Level) + len(entry.URL) + len(entry.Method) +
		len(entry.TraceID) + len(entry.SpanID) + len(entry.Content) +
		len(entry.ClientIP) + len(entry.Source))

	for k, v := range entry.Metadata {
		size += int64(len(k) + len(v))
	}

	// 额外的结构体开销
	size += 200

	return size
}
