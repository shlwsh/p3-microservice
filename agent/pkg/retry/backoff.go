// Package retry 实现指数退避重试机制。
//
// 核心算法：delay = baseDelay × multiplier^attempt + rand(0, expDelay × jitter)
// 该机制用于处理 Agent 与 Center 之间的瞬时通信故障，
// 避免惊群效应，并与固定缓存块协同确保日志不丢失。
package retry

import (
	"math"
	"math/rand"
	"time"
)

// BackoffConfig 定义指数退避的配置参数。
type BackoffConfig struct {
	// BaseDelay 基础延迟，第一次重试前的等待时间基数。
	// 论文默认值：200ms
	BaseDelay time.Duration `json:"base_delay" yaml:"base_delay"`

	// Multiplier 退避乘数，每次重试延迟的指数增长因子。
	// 论文默认值：2.0
	Multiplier float64 `json:"multiplier" yaml:"multiplier"`

	// MaxDelay 最大延迟上限，防止等待时间无限增长。
	// 论文默认值：30s
	MaxDelay time.Duration `json:"max_delay" yaml:"max_delay"`

	// MaxRetries 最大重试次数，超过后放弃并触发本地持久化。
	// 论文默认值：6
	MaxRetries int `json:"max_retries" yaml:"max_retries"`

	// Jitter 抖动因子 (0.0-1.0)，在计算出的延迟基础上添加随机偏移，
	// 用于打散多节点同时重试导致的惊群效应。
	// 论文默认值：0.3
	Jitter float64 `json:"jitter" yaml:"jitter"`
}

// DefaultConfig 返回论文中推荐的默认退避配置。
func DefaultConfig() *BackoffConfig {
	return &BackoffConfig{
		BaseDelay:  200 * time.Millisecond,
		Multiplier: 2.0,
		MaxDelay:   30 * time.Second,
		MaxRetries: 6,
		Jitter:     0.3,
	}
}

// NextDelay 计算第 attempt 次重试的等待延迟。
//
// 算法：
//  1. 计算指数延迟：expDelay = baseDelay × multiplier^attempt
//  2. 添加随机抖动：jitter = rand(0, expDelay × jitterFactor)
//  3. 总延迟 = expDelay + jitter
//  4. 钳制到 [0, maxDelay]
//
// 当 attempt >= MaxRetries 时返回 0，表示不再重试。
func (c *BackoffConfig) NextDelay(attempt int) time.Duration {
	if attempt >= c.MaxRetries {
		return 0
	}

	// 计算指数延迟
	expDelay := float64(c.BaseDelay) * math.Pow(c.Multiplier, float64(attempt))

	// 添加随机抖动
	jitter := rand.Float64() * expDelay * c.Jitter

	// 总延迟
	delay := time.Duration(expDelay + jitter)

	// 钳制到最大延迟
	if delay > c.MaxDelay {
		delay = c.MaxDelay
	}

	return delay
}

// NextDelayWithPressure 计算考虑系统压力的重试延迟。
// 当系统处于高压状态时（CPU/内存超阈值），延迟翻倍以降低负载。
func (c *BackoffConfig) NextDelayWithPressure(attempt int, isHighPressure bool) time.Duration {
	delay := c.NextDelay(attempt)
	if delay == 0 {
		return 0
	}
	if isHighPressure {
		delay *= 2
		if delay > c.MaxDelay {
			delay = c.MaxDelay
		}
	}
	return delay
}

// ShouldRetry 判断给定的重试次数是否仍可重试。
func (c *BackoffConfig) ShouldRetry(attempt int) bool {
	return attempt < c.MaxRetries
}

// TotalMaxDuration 估算所有重试的理论最大总耗时（不含抖动）。
// 用于设置全局超时。
func (c *BackoffConfig) TotalMaxDuration() time.Duration {
	var total time.Duration
	for i := 0; i < c.MaxRetries; i++ {
		expDelay := float64(c.BaseDelay) * math.Pow(c.Multiplier, float64(i))
		delay := time.Duration(expDelay * (1 + c.Jitter)) // 最大抖动
		if delay > c.MaxDelay {
			delay = c.MaxDelay
		}
		total += delay
	}
	return total
}

// RetryResult 记录一次重试执行的结果。
type RetryResult struct {
	Attempt     int           // 重试次数
	Delay       time.Duration // 实际等待延迟
	Success     bool          // 是否成功
	Error       error         // 错误信息
	Retryable   bool          // 错误是否可重试
	GaveUp      bool          // 是否放弃（超过最大重试次数）
	Persisted   bool          // 是否已本地持久化
}
