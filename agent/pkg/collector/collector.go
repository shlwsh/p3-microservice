// Package collector 实现日志采集模块。
package collector

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
	"github.com/p3-microservice/agent/pkg/matcher"
)

// Config 应用日志采集器配置。
type Config struct {
	ServiceName    string
	Matcher        *matcher.RuleMatcher
	Cache          *cache.FixedCacheBlock
	CollectionMode string        // directed | full
	LogInterval    time.Duration // 合成日志发射间隔
}

// NginxConfig Nginx 流量日志采集器配置。
type NginxConfig struct {
	PullURL      string
	ReadInterval time.Duration
	Cache        *cache.FixedCacheBlock
	ServiceName  string
}

// AppCollector 应用日志采集器。
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
func (c *AppCollector) Collect(entry *cache.LogEntry) {
	if entry.ServiceName == "" {
		entry.ServiceName = c.config.ServiceName
	}
	if !c.matcher.Match(entry) {
		return
	}
	if c.cache.AddLog(entry) {
		log.Printf("[AppCollector] 缓存达阈值，触发上传")
	}
}

// Run 启动采集器，模拟真实应用访问日志（Apache Combined 风格）。
func (c *AppCollector) Run(ctx context.Context) {
	interval := c.config.LogInterval
	if interval <= 0 {
		interval = 2 * time.Second
	}
	if c.config.CollectionMode == "full" {
		interval = 400 * time.Millisecond // 全量模式更高日志吞吐
	}
	log.Printf("[AppCollector] 应用日志采集器启动, service=%s, mode=%s, interval=%v",
		c.config.ServiceName, c.config.CollectionMode, interval)

	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	i := 0
	// 应用日志 URL 与网关 access log 路径一致，便于关注清单模式匹配
	apiPrefix := gatewayAPIPrefix(c.config.ServiceName)
	suffixes := []string{"/get", "/headers", "/ip", "/uuid", "/user-agent"}
	for {
		select {
		case <-ctx.Done():
			log.Println("[AppCollector] 应用日志采集器停止")
			return
		case <-ticker.C:
			i++
			path := apiPrefix + suffixes[i%len(suffixes)]
			level := "INFO"
			status := 200
			rt := 15 + i%80
			if i%12 == 0 {
				level = "ERROR"
				status = 500
				rt = 1200 + i%800
				path = apiPrefix + "/status/500"
			} else if i%7 == 0 {
				rt = 1100 + i%400
				path = apiPrefix + "/delay/1"
			}
			// 模拟真实 access log 行
			content := fmt.Sprintf(
				`%s - - [%s] "GET %s HTTP/1.1" %d %d "-" "python-requests/2.31" rt=%dms trace_id=trace-%s-%d`,
				"10.0.0."+fmt.Sprint(i%255),
				time.Now().Format("02/Jan/2006:15:04:05 -0700"),
				path, status, 512+i%2048, rt,
				c.config.ServiceName, i,
			)
			if c.config.CollectionMode == "full" && i%3 == 0 {
				content += " stack_trace=\"at handler.PayCheckout(line:142)...\""
			}
			c.Collect(&cache.LogEntry{
				LogID:          fmt.Sprintf("app-%s-%d", c.config.ServiceName, i),
				ServiceName:    c.config.ServiceName,
				Timestamp:      time.Now(),
				Level:          level,
				URL:            path,
				Method:         "GET",
				StatusCode:     status,
				ResponseTimeMs: int64(rt),
				TraceID:        fmt.Sprintf("trace-%s-%d", c.config.ServiceName, i),
				Source:         "APPLICATION",
				Content:        content,
			})
		}
	}
}

// NginxCollector Nginx 流量日志采集器。
type NginxCollector struct {
	config NginxConfig
	cache  *cache.FixedCacheBlock
	client *http.Client
}

// NewNginxCollector 创建 Nginx 流量日志采集器。
func NewNginxCollector(cfg NginxConfig) *NginxCollector {
	url := cfg.PullURL
	if url == "" {
		url = "http://127.0.0.1/_agent/logs"
	}
	return &NginxCollector{
		config: cfg,
		cache:  cfg.Cache,
		client: &http.Client{Timeout: 5 * time.Second},
	}
}

// Run 启动 Nginx 流量采集循环。
func (c *NginxCollector) Run(ctx context.Context) {
	log.Printf("[NginxCollector] Nginx 流量采集器启动, url=%s", c.config.PullURL)

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

type nginxPullResponse struct {
	Logs []struct {
		URL            string `json:"url"`
		Method         string `json:"method"`
		StatusCode     int    `json:"status_code"`
		ResponseTimeMs int64  `json:"response_time_ms"`
		ClientIP       string `json:"client_ip"`
		Timestamp      int64  `json:"timestamp"`
	} `json:"logs"`
	Count int `json:"count"`
}

func (c *NginxCollector) readAndProcess() {
	resp, err := c.client.Get(c.config.PullURL)
	if err != nil {
		log.Printf("[NginxCollector] 拉取失败: %v", err)
		return
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return
	}
	var payload nginxPullResponse
	if err := json.Unmarshal(body, &payload); err != nil {
		log.Printf("[NginxCollector] 解析失败: %v, body=%s", err, string(body[:min(len(body), 200)]))
		return
	}
	if len(payload.Logs) == 0 {
		return
	}
	for _, l := range payload.Logs {
		entry := &cache.LogEntry{
			LogID:          fmt.Sprintf("gw-%d", l.Timestamp),
			ServiceName:    c.config.ServiceName,
			Timestamp:      time.UnixMilli(l.Timestamp),
			Level:          "INFO",
			URL:            l.URL,
			Method:         l.Method,
			StatusCode:     l.StatusCode,
			ResponseTimeMs: l.ResponseTimeMs,
			ClientIP:       l.ClientIP,
			Source:         "GATEWAY",
			Content:        fmt.Sprintf(`{"url":"%s","status":%d,"rt":%d}`, l.URL, l.StatusCode, l.ResponseTimeMs),
		}
		c.cache.AddLog(entry)
	}
	log.Printf("[NginxCollector] 采集 %d 条网关流量日志", len(payload.Logs))
}

// gatewayAPIPrefix 将 Agent 服务名映射为网关对外 API 前缀（与 nginx location 一致）。
func gatewayAPIPrefix(serviceName string) string {
	name := strings.TrimPrefix(serviceName, "service-")
	if name == serviceName {
		return "/api/" + serviceName
	}
	return "/api/service" + name
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
