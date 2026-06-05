// Package config 负责加载和解析 Center 配置文件。
package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// CenterConfig 日志中心完整配置。
type CenterConfig struct {
	Server          ServerConfig          `yaml:"server"`
	Redis           RedisConfig           `yaml:"redis"`
	Loki            LokiConfig            `yaml:"loki"`
	Strategy        StrategyConfig        `yaml:"strategy"`
	URLCluster      URLClusterConfig      `yaml:"url_cluster"`
	SecondaryFilter SecondaryFilterConfig  `yaml:"secondary_filter"`
	Logging         LoggingConfig         `yaml:"logging"`
}

type ServerConfig struct {
	HTTPPort int `yaml:"http_port"`
	GRPCPort int `yaml:"grpc_port"`
}

type RedisConfig struct {
	Address  string `yaml:"address"`
	Password string `yaml:"password"`
	DB       int    `yaml:"db"`
	PoolSize int    `yaml:"pool_size"`
}

type LokiConfig struct {
	PushURL     string        `yaml:"push_url"`
	QueryURL    string        `yaml:"query_url"`
	TenantID    string        `yaml:"tenant_id"`
	BatchSize   int           `yaml:"batch_size"`
	BatchWaitMs int64         `yaml:"batch_wait_ms"`
	PushTimeout time.Duration `yaml:"push_timeout"`
	MaxRetries  int           `yaml:"max_retries"`
}

type StrategyConfig struct {
	ResponseTimeThresholdMs int64   `yaml:"response_time_threshold_ms"`
	ErrorCodes              []int   `yaml:"error_codes"`
	ErrorRateThreshold      float64 `yaml:"error_rate_threshold"`
	GenerationIntervalSec   int64   `yaml:"generation_interval_sec"`
	AttentionListTTLSec     int64   `yaml:"attention_list_ttl_sec"`
	TopK                    int     `yaml:"top_k"`
	TimeWindowSec           int64   `yaml:"time_window_sec"`
}

type URLClusterConfig struct {
	EnableNumericReplace bool    `yaml:"enable_numeric_replace"`
	EnableUUIDReplace    bool    `yaml:"enable_uuid_replace"`
	SimilarityThreshold  float64 `yaml:"similarity_threshold"`
}

type SecondaryFilterConfig struct {
	Enabled        bool  `yaml:"enabled"`
	DedupWindowSec int64 `yaml:"dedup_window_sec"`
}

type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"`
}

// Load 从指定路径加载 Center 配置。
func Load(path string) (*CenterConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	cfg := &CenterConfig{}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %w", err)
	}

	cfg.applyDefaults()

	if err := cfg.validate(); err != nil {
		return nil, fmt.Errorf("配置验证失败: %w", err)
	}

	return cfg, nil
}

func (c *CenterConfig) applyDefaults() {
	if c.Server.HTTPPort == 0 {
		c.Server.HTTPPort = 8080
	}
	if c.Server.GRPCPort == 0 {
		c.Server.GRPCPort = 9090
	}
	if c.Redis.Address == "" {
		c.Redis.Address = "localhost:6379"
	}
	if c.Redis.PoolSize == 0 {
		c.Redis.PoolSize = 20
	}
	if c.Loki.PushURL == "" {
		c.Loki.PushURL = "http://localhost:3100/loki/api/v1/push"
	}
	if c.Loki.QueryURL == "" {
		c.Loki.QueryURL = "http://localhost:3100/loki/api/v1/query_range"
	}
	if c.Loki.BatchSize == 0 {
		c.Loki.BatchSize = 100
	}
	if c.Loki.BatchWaitMs == 0 {
		c.Loki.BatchWaitMs = 1000
	}
	if c.Loki.PushTimeout == 0 {
		c.Loki.PushTimeout = 10 * time.Second
	}
	if c.Loki.MaxRetries == 0 {
		c.Loki.MaxRetries = 3
	}
	if c.Strategy.ResponseTimeThresholdMs == 0 {
		c.Strategy.ResponseTimeThresholdMs = 1000
	}
	if len(c.Strategy.ErrorCodes) == 0 {
		c.Strategy.ErrorCodes = []int{500, 502, 503, 504}
	}
	if c.Strategy.GenerationIntervalSec == 0 {
		c.Strategy.GenerationIntervalSec = 30
	}
	if c.Strategy.AttentionListTTLSec == 0 {
		c.Strategy.AttentionListTTLSec = 300
	}
	if c.Strategy.TopK == 0 {
		c.Strategy.TopK = 50
	}
	if c.Strategy.TimeWindowSec == 0 {
		c.Strategy.TimeWindowSec = 60
	}
}

func (c *CenterConfig) validate() error {
	if c.Loki.PushURL == "" {
		return fmt.Errorf("loki.push_url 不能为空")
	}
	if c.Strategy.TopK <= 0 {
		return fmt.Errorf("strategy.top_k 必须大于 0")
	}
	return nil
}
