// Package config 负责加载和解析 Agent 配置文件。
package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// AgentConfig 是 Agent 的完整配置结构。
type AgentConfig struct {
	Server       ServerConfig       `yaml:"server"`
	Cache        CacheConfig        `yaml:"cache"`
	Retry        RetryConfig        `yaml:"retry"`
	Matcher      MatcherConfig      `yaml:"matcher"`
	Monitor      MonitorConfig      `yaml:"monitor"`
	LocalPersist LocalPersistConfig `yaml:"local_persist"`
	Nginx        NginxConfig        `yaml:"nginx"`
	Metrics      MetricsConfig      `yaml:"metrics"`
	Logging      LoggingConfig      `yaml:"logging"`
}

type ServerConfig struct {
	CenterAddress string `yaml:"center_address"`
	AgentID       string `yaml:"agent_id"`
	ServiceName   string `yaml:"service_name"`
}

type CacheConfig struct {
	MaxSizeBytes          int64 `yaml:"max_size_bytes"`
	MaxEntries            int   `yaml:"max_entries"`
	FlushThresholdPercent int   `yaml:"flush_threshold_percent"`
	FlushIntervalMs       int64 `yaml:"flush_interval_ms"`
	EnableCompression     bool  `yaml:"enable_compression"`
}

type RetryConfig struct {
	BaseDelay  time.Duration `yaml:"base_delay"`
	Multiplier float64       `yaml:"multiplier"`
	MaxDelay   time.Duration `yaml:"max_delay"`
	MaxRetries int           `yaml:"max_retries"`
	Jitter     float64       `yaml:"jitter"`
}

type MatcherConfig struct {
	PullInterval time.Duration `yaml:"pull_interval"`
	MinLogLevel  string        `yaml:"min_log_level"`
}

type MonitorConfig struct {
	SampleInterval      time.Duration `yaml:"sample_interval"`
	CPUHighThreshold    float64       `yaml:"cpu_high_threshold"`
	MemoryHighThreshold float64       `yaml:"memory_high_threshold"`
}

type LocalPersistConfig struct {
	DBPath       string `yaml:"db_path"`
	MaxSizeBytes int64  `yaml:"max_size_bytes"`
}

type NginxConfig struct {
	Enabled          bool          `yaml:"enabled"`
	SharedMemoryPath string        `yaml:"shared_memory_path"`
	ReadInterval     time.Duration `yaml:"read_interval"`
}

type MetricsConfig struct {
	Enabled bool   `yaml:"enabled"`
	Port    int    `yaml:"port"`
	Path    string `yaml:"path"`
}

type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"`
	Output string `yaml:"output"`
}

// Load 从指定路径加载配置文件。
func Load(path string) (*AgentConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	cfg := &AgentConfig{}
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %w", err)
	}

	// 应用默认值
	cfg.applyDefaults()

	// 验证配置
	if err := cfg.validate(); err != nil {
		return nil, fmt.Errorf("配置验证失败: %w", err)
	}

	return cfg, nil
}

// applyDefaults 为未设置的字段填充默认值。
func (c *AgentConfig) applyDefaults() {
	if c.Cache.MaxSizeBytes == 0 {
		c.Cache.MaxSizeBytes = 128 * 1024 * 1024 // 128MB
	}
	if c.Cache.MaxEntries == 0 {
		c.Cache.MaxEntries = 100000
	}
	if c.Cache.FlushThresholdPercent == 0 {
		c.Cache.FlushThresholdPercent = 80
	}
	if c.Cache.FlushIntervalMs == 0 {
		c.Cache.FlushIntervalMs = 5000
	}
	if c.Retry.BaseDelay == 0 {
		c.Retry.BaseDelay = 200 * time.Millisecond
	}
	if c.Retry.Multiplier == 0 {
		c.Retry.Multiplier = 2.0
	}
	if c.Retry.MaxDelay == 0 {
		c.Retry.MaxDelay = 30 * time.Second
	}
	if c.Retry.MaxRetries == 0 {
		c.Retry.MaxRetries = 6
	}
	if c.Retry.Jitter == 0 {
		c.Retry.Jitter = 0.3
	}
	if c.Matcher.PullInterval == 0 {
		c.Matcher.PullInterval = 10 * time.Second
	}
	if c.Monitor.SampleInterval == 0 {
		c.Monitor.SampleInterval = 5 * time.Second
	}
	if c.Monitor.CPUHighThreshold == 0 {
		c.Monitor.CPUHighThreshold = 0.80
	}
	if c.Monitor.MemoryHighThreshold == 0 {
		c.Monitor.MemoryHighThreshold = 0.85
	}
	if c.Metrics.Port == 0 {
		c.Metrics.Port = 9100
	}
	if c.Metrics.Path == "" {
		c.Metrics.Path = "/metrics"
	}
}

// validate 验证配置的合法性。
func (c *AgentConfig) validate() error {
	if c.Server.CenterAddress == "" {
		return fmt.Errorf("server.center_address 不能为空")
	}
	if c.Cache.MaxSizeBytes < 1024*1024 {
		return fmt.Errorf("cache.max_size_bytes 不能小于 1MB")
	}
	if c.Retry.Jitter < 0 || c.Retry.Jitter > 1.0 {
		return fmt.Errorf("retry.jitter 必须在 [0.0, 1.0] 范围内")
	}
	if c.Monitor.CPUHighThreshold <= 0 || c.Monitor.CPUHighThreshold > 1.0 {
		return fmt.Errorf("monitor.cpu_high_threshold 必须在 (0.0, 1.0] 范围内")
	}
	return nil
}
