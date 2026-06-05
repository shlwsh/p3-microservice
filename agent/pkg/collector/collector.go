// Package collector 实现日志采集模块。
//
// 包含两类采集器：
// - AppCollector：应用日志采集（通用微服务节点）
// - NginxCollector：Nginx 流量日志采集（网关节点）
package collector

import (
	"context"
	"log"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
	"github.com/p3-microservice/agent/pkg/matcher"
)

// Config 应用日志采集器配置。
type Config struct {
	ServiceName string
	Matcher     *matcher.RuleMatcher
	Cache       *cache.FixedCacheBlock
}

// NginxConfig Nginx 流量日志采集器配置。
type NginxConfig struct {
	SharedMemoryPath string
	ReadInterval     time.Duration
	Cache            *cache.FixedCacheBlock
}

// AppCollector 应用日志采集器。
// 作为 SDK 嵌入微服务，拦截应用产生的日志并按规则过滤后写入缓存。
type AppCollector struct {
	config  Config
	matcher *matcher.RuleMatcher
	cache   *cache.FixedCacheBlock
}

// NewAppCollector 创建应用日志采集器。
func NewAppCollector(cfg Config) *AppCollector {
	return &AppCollector{
		config:  cfg,
		matcher: cfg.Matcher,
		cache:   cfg.Cache,
	}
}

// Collect 采集一条日志。
// 该方法应在应用日志框架的 Hook 中调用。
// 只有匹配关注清单的日志才会写入缓存。
func (c *AppCollector) Collect(entry *cache.LogEntry) {
	// 填充服务名
	if entry.ServiceName == "" {
		entry.ServiceName = c.config.ServiceName
	}

	// 定向匹配
	if !c.matcher.Match(entry) {
		return // 不在关注清单中，丢弃
	}

	// 写入固定缓存块
	shouldFlush := c.cache.AddLog(entry)
	if shouldFlush {
		log.Printf("[AppCollector] 缓存达阈值，触发上传")
	}
}

// Run 启动采集器（SDK 模式下为空循环，仅保持上下文活跃）。
func (c *AppCollector) Run(ctx context.Context) {
	log.Printf("[AppCollector] 应用日志采集器启动, service=%s", c.config.ServiceName)
	<-ctx.Done()
	log.Println("[AppCollector] 应用日志采集器停止")
}

// NginxCollector Nginx 流量日志采集器。
// 从 Nginx 共享内存或日志文件中读取流量数据。
type NginxCollector struct {
	config NginxConfig
	cache  *cache.FixedCacheBlock
}

// NewNginxCollector 创建 Nginx 流量日志采集器。
func NewNginxCollector(cfg NginxConfig) *NginxCollector {
	return &NginxCollector{
		config: cfg,
		cache:  cfg.Cache,
	}
}

// Run 启动 Nginx 流量采集循环。
func (c *NginxCollector) Run(ctx context.Context) {
	log.Printf("[NginxCollector] Nginx 流量采集器启动, path=%s", c.config.SharedMemoryPath)

	ticker := time.NewTicker(c.config.ReadInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("[NginxCollector] Nginx 流量采集器停止")
			return
		case <-ticker.C:
			c.readAndProcess()
		}
	}
}

// readAndProcess 从 Nginx 共享内存读取并处理流量日志。
func (c *NginxCollector) readAndProcess() {
	// TODO: 实际实现：读取共享内存 / 日志文件
	// entries := readFromSharedMemory(c.config.SharedMemoryPath)
	// for _, entry := range entries {
	//     entry.Source = "GATEWAY"
	//     c.cache.AddLog(entry)
	// }
}
