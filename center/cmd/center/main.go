// Package main 是分布式定向日志采集组件的日志中心入口。
//
// 日志中心是主节点，负责：
// 1. 接收 Agent 上传的日志（gRPC）
// 2. 动态生成关注清单（基于网关流量分析）
// 3. 下发规则到各 Agent 节点
// 4. 二次过滤与结构化转换
// 5. 存储至 Loki
package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/p3-microservice/center/pkg/config"
	"github.com/p3-microservice/center/pkg/dispatch"
	"github.com/p3-microservice/center/pkg/grpcserver"
	"github.com/p3-microservice/center/pkg/receiver"
	"github.com/p3-microservice/center/pkg/storage"
	"github.com/p3-microservice/center/pkg/strategy"

	"google.golang.org/grpc"
)

func main() {
	fmt.Println("==============================================")
	fmt.Println(" Distributed Directed Log Collector - Center")
	fmt.Println(" 分布式定向日志采集组件 - 日志中心 (Go)")
	fmt.Println("==============================================")

	// ========================================
	// 1. 加载配置
	// ========================================
	cfgPath := getConfigPath()
	cfg, err := config.Load(cfgPath)
	if err != nil {
		log.Fatalf("[Center] 配置加载失败: %v", err)
	}
	log.Printf("[Center] 配置加载成功")

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// ========================================
	// 2. 初始化各模块
	// ========================================

	// 2.1 Loki 存储适配器
	lokiStore, err := storage.NewLokiStore(storage.LokiConfig{
		PushURL:     cfg.Loki.PushURL,
		QueryURL:    cfg.Loki.QueryURL,
		TenantID:    cfg.Loki.TenantID,
		BatchSize:   cfg.Loki.BatchSize,
		BatchWaitMs: cfg.Loki.BatchWaitMs,
		PushTimeout: cfg.Loki.PushTimeout,
		MaxRetries:  cfg.Loki.MaxRetries,
	})
	if err != nil {
		log.Fatalf("[Center] Loki 存储初始化失败: %v", err)
	}

	// 2.2 高价值过滤器
	hvFilter := strategy.NewHighValueFilter(strategy.HighValueFilterConfig{
		ResponseTimeThresholdMs: cfg.Strategy.ResponseTimeThresholdMs,
		ErrorCodes:              cfg.Strategy.ErrorCodes,
		ErrorRateThreshold:      cfg.Strategy.ErrorRateThreshold,
	})

	// 2.3 URL 聚类器
	urlCluster := strategy.NewURLClusterer(strategy.URLClusterConfig{
		EnableNumericReplace: cfg.URLCluster.EnableNumericReplace,
		EnableUUIDReplace:    cfg.URLCluster.EnableUUIDReplace,
		SimilarityThreshold:  cfg.URLCluster.SimilarityThreshold,
	})

	// 2.4 关注清单生成器
	listGen := strategy.NewAttentionListGenerator(strategy.AttentionListConfig{
		TopK:       cfg.Strategy.TopK,
		TTLSeconds: cfg.Strategy.AttentionListTTLSec,
		Filter:     hvFilter,
		Clusterer:  urlCluster,
	})

	// 2.5 规则下发管理器
	dispatcher := dispatch.NewRuleDispatcher()

	// 2.6 日志接收与二次过滤
	logReceiver := receiver.NewLogReceiver(receiver.Config{
		Store:           lokiStore,
		SecondaryFilter: cfg.SecondaryFilter.Enabled,
		DedupWindowSec:  cfg.SecondaryFilter.DedupWindowSec,
	})

	// 2.7 三次转换引擎
	transformer := strategy.NewTripleTransformer(strategy.TripleTransformConfig{
		ListGenerator: listGen,
		Dispatcher:    dispatcher,
		Receiver:      logReceiver,
	})

	// ========================================
	// 3. 启动服务
	// ========================================
	var wg sync.WaitGroup

	// 3.1 启动 gRPC 服务
	grpcSrv := grpcserver.NewServer(grpcserver.Config{
		LogReceiver: logReceiver,
		Dispatcher:  dispatcher,
		ListGen:     listGen,
	})

	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", cfg.Server.GRPCPort))
	if err != nil {
		log.Fatalf("[Center] gRPC 监听失败: %v", err)
	}

	grpcServer := grpc.NewServer()
	grpcSrv.Register(grpcServer)

	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Printf("[Center] gRPC 服务启动在 :%d", cfg.Server.GRPCPort)
		if err := grpcServer.Serve(lis); err != nil {
			log.Printf("[Center] gRPC 服务异常: %v", err)
		}
	}()

	// 3.2 启动 HTTP API
	httpMux := http.NewServeMux()
	httpMux.HandleFunc("/api/v1/health", healthHandler)
	httpMux.HandleFunc("/api/v1/attention-list", listGen.HTTPHandler)
	httpMux.HandleFunc("/api/v1/agents", dispatcher.HTTPAgentListHandler)

	httpServer := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Server.HTTPPort),
		Handler: httpMux,
	}

	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Printf("[Center] HTTP API 启动在 :%d", cfg.Server.HTTPPort)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("[Center] HTTP 服务异常: %v", err)
		}
	}()

	// 3.3 启动定向清单周期性生成
	wg.Add(1)
	go func() {
		defer wg.Done()
		transformer.RunPeriodicGeneration(ctx,
			time.Duration(cfg.Strategy.GenerationIntervalSec)*time.Second)
	}()

	// 3.4 启动 Loki 批量推送
	wg.Add(1)
	go func() {
		defer wg.Done()
		lokiStore.RunBatchPusher(ctx)
	}()

	log.Println("[Center] 所有模块启动完毕")

	// ========================================
	// 4. 优雅关闭
	// ========================================
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh
	log.Printf("[Center] 收到信号 %v，开始优雅关闭...", sig)

	cancel()

	// 关闭 HTTP
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	httpServer.Shutdown(shutdownCtx)

	// 关闭 gRPC
	grpcServer.GracefulStop()

	// 刷新 Loki 缓冲区
	lokiStore.Flush()

	wg.Wait()
	log.Println("[Center] 退出完毕")
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok","component":"log-center"}`))
}

func getConfigPath() string {
	path := os.Getenv("CENTER_CONFIG_PATH")
	if path != "" {
		return path
	}
	candidates := []string{
		"./configs/center.yaml",
		"/etc/center/center.yaml",
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p
		}
	}
	return candidates[0]
}
