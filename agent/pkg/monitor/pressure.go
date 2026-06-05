// Package monitor 实现节点资源监控。
//
// 通过采样 CPU 和内存使用率，判断当前节点是否处于高压状态。
// 高压状态下，指数退避机制会延长重试间隔以降低系统负载。
package monitor

import (
	"context"
	"log"
	"runtime"
	"sync/atomic"
	"time"
)

// Config 资源监控配置。
type Config struct {
	SampleInterval      time.Duration // 采样间隔
	CPUHighThreshold    float64       // CPU 高压阈值 (0.0-1.0)
	MemoryHighThreshold float64       // 内存高压阈值 (0.0-1.0)
}

// ResourceMonitor 资源监控器。
type ResourceMonitor struct {
	config       Config
	highPressure atomic.Bool    // 是否处于高压状态
	cpuUsage     atomic.Int64   // CPU 使用率 × 10000（定点数）
	memUsage     atomic.Int64   // 内存使用率 × 10000
}

// NewResourceMonitor 创建资源监控器。
func NewResourceMonitor(cfg Config) *ResourceMonitor {
	return &ResourceMonitor{
		config: cfg,
	}
}

// Run 启动资源监控循环。
func (m *ResourceMonitor) Run(ctx context.Context) {
	ticker := time.NewTicker(m.config.SampleInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("[Monitor] 资源监控停止")
			return
		case <-ticker.C:
			m.sample()
		}
	}
}

// sample 执行一次资源采样。
func (m *ResourceMonitor) sample() {
	// 内存使用率
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	// 使用 HeapAlloc/HeapSys 近似内存使用率
	memUsage := float64(memStats.HeapAlloc) / float64(memStats.HeapSys+1)
	m.memUsage.Store(int64(memUsage * 10000))

	// CPU 使用率（简化实现：通过 goroutine 数量和 NumCPU 估算）
	// 生产环境应读取 /proc/stat 或使用 cgroups 信息
	numGoroutine := runtime.NumGoroutine()
	numCPU := runtime.NumCPU()
	cpuEstimate := float64(numGoroutine) / float64(numCPU*100) // 粗略估算
	if cpuEstimate > 1.0 {
		cpuEstimate = 1.0
	}
	m.cpuUsage.Store(int64(cpuEstimate * 10000))

	// 判断高压状态
	isHigh := memUsage >= m.config.MemoryHighThreshold || cpuEstimate >= m.config.CPUHighThreshold
	m.highPressure.Store(isHigh)

	if isHigh {
		log.Printf("[Monitor] 高压状态: CPU=%.2f%%, Mem=%.2f%%",
			cpuEstimate*100, memUsage*100)
	}
}

// IsHighPressure 返回当前是否处于高压状态。
// 该方法线程安全，可被重试机制等模块并发调用。
func (m *ResourceMonitor) IsHighPressure() bool {
	return m.highPressure.Load()
}

// CPUUsage 返回最近一次采样的 CPU 使用率 (0.0-1.0)。
func (m *ResourceMonitor) CPUUsage() float64 {
	return float64(m.cpuUsage.Load()) / 10000
}

// MemoryUsage 返回最近一次采样的内存使用率 (0.0-1.0)。
func (m *ResourceMonitor) MemoryUsage() float64 {
	return float64(m.memUsage.Load()) / 10000
}

// Status 返回当前资源状态快照。
func (m *ResourceMonitor) Status() ResourceStatus {
	return ResourceStatus{
		CPUUsage:     m.CPUUsage(),
		MemoryUsage:  m.MemoryUsage(),
		HighPressure: m.IsHighPressure(),
		NumGoroutine: runtime.NumGoroutine(),
		NumCPU:       runtime.NumCPU(),
	}
}

// ResourceStatus 资源状态快照。
type ResourceStatus struct {
	CPUUsage     float64 `json:"cpu_usage"`
	MemoryUsage  float64 `json:"memory_usage"`
	HighPressure bool    `json:"high_pressure"`
	NumGoroutine int     `json:"num_goroutine"`
	NumCPU       int     `json:"num_cpu"`
}
