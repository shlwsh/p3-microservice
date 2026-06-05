// Package main 是分布式定向日志采集组件的节点采集器入口。
// 它负责初始化配置、启动各模块（缓存、采集、匹配、上传、监控），
// 并通过 gRPC 与日志中心通信。
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
	"github.com/p3-microservice/agent/pkg/collector"
	"github.com/p3-microservice/agent/pkg/config"
	"github.com/p3-microservice/agent/pkg/matcher"
	"github.com/p3-microservice/agent/pkg/metrics"
	"github.com/p3-microservice/agent/pkg/monitor"
	"github.com/p3-microservice/agent/pkg/retry"
	"github.com/p3-microservice/agent/pkg/uploader"
)

func main() {
	// ========================================
	// 1. 加载配置
	// ========================================
	cfgPath := getConfigPath()
	cfg, err := config.Load(cfgPath)
	if err != nil {
		log.Fatalf("[Agent] 配置加载失败: %v", err)
	}
	log.Printf("[Agent] 配置加载成功, agentId=%s, service=%s", cfg.Server.AgentID, cfg.Server.ServiceName)

	// ========================================
	// 2. 初始化各模块
	// ========================================
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 2.1 资源监控
	mon := monitor.NewResourceMonitor(monitor.Config{
		SampleInterval:      cfg.Monitor.SampleInterval,
		CPUHighThreshold:    cfg.Monitor.CPUHighThreshold,
		MemoryHighThreshold: cfg.Monitor.MemoryHighThreshold,
	})

	// 2.2 指数退避重试配置
	backoffCfg := &retry.BackoffConfig{
		BaseDelay:  cfg.Retry.BaseDelay,
		Multiplier: cfg.Retry.Multiplier,
		MaxDelay:   cfg.Retry.MaxDelay,
		MaxRetries: cfg.Retry.MaxRetries,
		Jitter:     cfg.Retry.Jitter,
	}

	// 2.3 固定缓存块
	cacheBlock := cache.NewFixedCacheBlock(cache.Config{
		MaxSizeBytes:          cfg.Cache.MaxSizeBytes,
		MaxEntries:            cfg.Cache.MaxEntries,
		FlushThresholdPercent: cfg.Cache.FlushThresholdPercent,
		FlushIntervalMs:       cfg.Cache.FlushIntervalMs,
		EnableCompression:     cfg.Cache.EnableCompression,
	})

	// 2.4 gRPC 上传器
	up, err := uploader.NewGRPCUploader(uploader.Config{
		CenterAddress: cfg.Server.CenterAddress,
		AgentID:       cfg.Server.AgentID,
		BackoffConfig: backoffCfg,
		Monitor:       mon,
		LocalPersist: uploader.LocalPersistConfig{
			DBPath:       cfg.LocalPersist.DBPath,
			MaxSizeBytes: cfg.LocalPersist.MaxSizeBytes,
		},
	})
	if err != nil {
		log.Fatalf("[Agent] gRPC 上传器初始化失败: %v", err)
	}

	// 2.5 规则匹配器
	ruleMatcher := matcher.NewRuleMatcher(matcher.Config{
		PullInterval: cfg.Matcher.PullInterval,
		MinLogLevel:  cfg.Matcher.MinLogLevel,
	})

	// 2.6 日志采集器
	appCollector := collector.NewAppCollector(collector.Config{
		ServiceName: cfg.Server.ServiceName,
		Matcher:     ruleMatcher,
		Cache:       cacheBlock,
	})

	// 2.7 Nginx 采集器（仅网关节点）
	var nginxCollector *collector.NginxCollector
	if cfg.Nginx.Enabled {
		nginxCollector = collector.NewNginxCollector(collector.NginxConfig{
			SharedMemoryPath: cfg.Nginx.SharedMemoryPath,
			ReadInterval:     cfg.Nginx.ReadInterval,
			Cache:            cacheBlock,
		})
	}

	// 2.8 Prometheus 指标
	if cfg.Metrics.Enabled {
		metrics.StartServer(cfg.Metrics.Port, cfg.Metrics.Path)
	}

	// ========================================
	// 3. 启动各模块
	// ========================================
	var wg sync.WaitGroup

	// 启动资源监控
	wg.Add(1)
	go func() {
		defer wg.Done()
		mon.Run(ctx)
	}()

	// 启动缓存块（含异步上传触发）
	wg.Add(1)
	go func() {
		defer wg.Done()
		cacheBlock.Run(ctx, up)
	}()

	// 启动规则拉取
	wg.Add(1)
	go func() {
		defer wg.Done()
		ruleMatcher.StartPulling(ctx, up.GetRuleClient())
	}()

	// 启动应用日志采集
	wg.Add(1)
	go func() {
		defer wg.Done()
		appCollector.Run(ctx)
	}()

	// 启动 Nginx 采集（若启用）
	if nginxCollector != nil {
		wg.Add(1)
		go func() {
			defer wg.Done()
			nginxCollector.Run(ctx)
		}()
	}

	// 启动心跳上报
	wg.Add(1)
	go func() {
		defer wg.Done()
		up.StartHeartbeat(ctx, mon, 10*time.Second)
	}()

	log.Printf("[Agent] 所有模块启动完毕，等待信号...")

	// ========================================
	// 4. 优雅关闭
	// ========================================
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh
	log.Printf("[Agent] 收到信号 %v，开始优雅关闭...", sig)

	// 取消上下文，通知所有 goroutine 停止
	cancel()

	// 等待所有 goroutine 退出（最多 30 秒）
	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		log.Println("[Agent] 所有模块已安全退出")
	case <-time.After(30 * time.Second):
		log.Println("[Agent] 超时强制退出")
	}

	// 刷新剩余缓存
	if err := cacheBlock.FlushAll(up); err != nil {
		log.Printf("[Agent] 刷新缓存失败: %v", err)
	}

	// 关闭 gRPC 连接
	up.Close()

	log.Println("[Agent] 退出完毕")
}

// getConfigPath 获取配置文件路径
func getConfigPath() string {
	path := os.Getenv("AGENT_CONFIG_PATH")
	if path != "" {
		return path
	}
	// 默认路径
	candidates := []string{
		"./configs/agent.yaml",
		"/etc/agent/agent.yaml",
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return candidates[0]
}

func init() {
	fmt.Println("==============================================")
	fmt.Println(" Distributed Directed Log Collector - Agent")
	fmt.Println(" 分布式定向日志采集组件 - 节点采集器")
	fmt.Println("==============================================")
}
