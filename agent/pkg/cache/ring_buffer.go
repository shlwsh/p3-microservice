// Package cache 实现固定缓存块算法。
//
// 核心设计：每个节点分配固定内存块（64-256MB），使用环形队列缓存日志条目。
// 当缓存达到阈值时触发异步上传，超容量时覆盖最旧条目并计数丢弃量。
// 支持 gzip 压缩以减少网络传输量。
package cache

import (
	"container/ring"
	"sync"
	"sync/atomic"
	"time"
)

// LogEntry 表示一条日志条目。
type LogEntry struct {
	LogID         string            `json:"log_id"`
	ServiceName   string            `json:"service_name"`
	InstanceID    string            `json:"instance_id"`
	Timestamp     time.Time         `json:"timestamp"`
	Level         string            `json:"level"`
	URL           string            `json:"url"`
	Method        string            `json:"method"`
	StatusCode    int               `json:"status_code"`
	ResponseTimeMs int64            `json:"response_time_ms"`
	TraceID       string            `json:"trace_id"`
	SpanID        string            `json:"span_id"`
	Content       string            `json:"content"`
	ClientIP      string            `json:"client_ip"`
	Source        string            `json:"source"`
	Metadata      map[string]string `json:"metadata"`
	SizeBytes     int64             `json:"-"` // 估算的内存占用
}

// RingBuffer 是基于 container/ring 的环形队列缓存。
// 提供固定容量的 FIFO 缓存，满时覆盖最旧条目。
type RingBuffer struct {
	mu          sync.Mutex
	ring        *ring.Ring
	capacity    int       // 最大条目数
	count       int       // 当前条目数
	sizeBytes   int64     // 当前总字节数
	droppedCount atomic.Int64 // 因容量溢出被丢弃的条目数
}

// NewRingBuffer 创建指定容量的环形缓存。
func NewRingBuffer(capacity int) *RingBuffer {
	return &RingBuffer{
		ring:     ring.New(capacity),
		capacity: capacity,
	}
}

// Push 向环形缓存中添加一条日志条目。
// 如果缓存已满，最旧的条目将被覆盖。
func (rb *RingBuffer) Push(entry *LogEntry) {
	rb.mu.Lock()
	defer rb.mu.Unlock()

	// 如果当前位置已有数据，说明缓存已满，需要覆盖
	if rb.ring.Value != nil && rb.count >= rb.capacity {
		old := rb.ring.Value.(*LogEntry)
		rb.sizeBytes -= old.SizeBytes
		rb.droppedCount.Add(1)
	} else if rb.count < rb.capacity {
		rb.count++
	}

	rb.ring.Value = entry
	rb.sizeBytes += entry.SizeBytes
	rb.ring = rb.ring.Next()
}

// DrainBatch 从缓存中取出最多 maxBatch 条日志。
// 取出的条目从缓存中移除。
func (rb *RingBuffer) DrainBatch(maxBatch int) []*LogEntry {
	rb.mu.Lock()
	defer rb.mu.Unlock()

	if rb.count == 0 {
		return nil
	}

	batchSize := maxBatch
	if batchSize > rb.count {
		batchSize = rb.count
	}

	batch := make([]*LogEntry, 0, batchSize)

	// 从当前写入位置之前回溯 count 个位置开始读取
	readPos := rb.ring.Move(-rb.count)
	for i := 0; i < batchSize; i++ {
		if readPos.Value != nil {
			batch = append(batch, readPos.Value.(*LogEntry))
			rb.sizeBytes -= readPos.Value.(*LogEntry).SizeBytes
			readPos.Value = nil
		}
		readPos = readPos.Next()
	}

	rb.count -= len(batch)
	return batch
}

// Count 返回当前缓存的条目数。
func (rb *RingBuffer) Count() int {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	return rb.count
}

// SizeBytes 返回当前缓存的总字节数。
func (rb *RingBuffer) SizeBytes() int64 {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	return rb.sizeBytes
}

// DroppedCount 返回因容量溢出被丢弃的条目总数。
func (rb *RingBuffer) DroppedCount() int64 {
	return rb.droppedCount.Load()
}

// UsagePercent 返回当前缓存使用率（0-100）。
func (rb *RingBuffer) UsagePercent() int {
	rb.mu.Lock()
	defer rb.mu.Unlock()
	if rb.capacity == 0 {
		return 0
	}
	return rb.count * 100 / rb.capacity
}

// Reset 清空缓存。
func (rb *RingBuffer) Reset() {
	rb.mu.Lock()
	defer rb.mu.Unlock()

	rb.ring.Do(func(val interface{}) {
		// ring.Do 遍历所有节点
	})
	rb.ring = ring.New(rb.capacity)
	rb.count = 0
	rb.sizeBytes = 0
}
