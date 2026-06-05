package retry

import (
	"math"
	"testing"
	"time"
)

// TestDefaultConfig 验证默认配置与论文推荐值一致。
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.BaseDelay != 200*time.Millisecond {
		t.Errorf("BaseDelay = %v, 期望 200ms", cfg.BaseDelay)
	}
	if cfg.Multiplier != 2.0 {
		t.Errorf("Multiplier = %v, 期望 2.0", cfg.Multiplier)
	}
	if cfg.MaxDelay != 30*time.Second {
		t.Errorf("MaxDelay = %v, 期望 30s", cfg.MaxDelay)
	}
	if cfg.MaxRetries != 6 {
		t.Errorf("MaxRetries = %d, 期望 6", cfg.MaxRetries)
	}
	if cfg.Jitter != 0.3 {
		t.Errorf("Jitter = %v, 期望 0.3", cfg.Jitter)
	}
}

// TestNextDelay_ExponentialGrowth 验证延迟呈指数增长趋势。
func TestNextDelay_ExponentialGrowth(t *testing.T) {
	cfg := &BackoffConfig{
		BaseDelay:  200 * time.Millisecond,
		Multiplier: 2.0,
		MaxDelay:   30 * time.Second,
		MaxRetries: 6,
		Jitter:     0, // 关闭抖动以确定性测试
	}

	// 期望值：200ms, 400ms, 800ms, 1600ms, 3200ms, 6400ms
	expected := []time.Duration{
		200 * time.Millisecond,
		400 * time.Millisecond,
		800 * time.Millisecond,
		1600 * time.Millisecond,
		3200 * time.Millisecond,
		6400 * time.Millisecond,
	}

	for i, exp := range expected {
		got := cfg.NextDelay(i)
		if got != exp {
			t.Errorf("attempt %d: 延迟 = %v, 期望 %v", i, got, exp)
		}
	}
}

// TestNextDelay_MaxDelayClamp 验证延迟不超过 MaxDelay。
func TestNextDelay_MaxDelayClamp(t *testing.T) {
	cfg := &BackoffConfig{
		BaseDelay:  1 * time.Second,
		Multiplier: 3.0,
		MaxDelay:   10 * time.Second,
		MaxRetries: 10,
		Jitter:     0,
	}

	// attempt=3: 1 * 3^3 = 27s，应被钳制到 10s
	got := cfg.NextDelay(3)
	if got != 10*time.Second {
		t.Errorf("attempt 3: 延迟 = %v, 期望被钳制到 10s", got)
	}
}

// TestNextDelay_MaxRetriesExceeded 验证超过最大重试次数后返回 0。
func TestNextDelay_MaxRetriesExceeded(t *testing.T) {
	cfg := DefaultConfig()

	got := cfg.NextDelay(6) // attempt == MaxRetries
	if got != 0 {
		t.Errorf("attempt=%d (==MaxRetries): 延迟 = %v, 期望 0", 6, got)
	}

	got = cfg.NextDelay(100) // 远超 MaxRetries
	if got != 0 {
		t.Errorf("attempt=100: 延迟 = %v, 期望 0", got)
	}
}

// TestNextDelay_JitterRange 验证抖动在合法范围内。
func TestNextDelay_JitterRange(t *testing.T) {
	cfg := &BackoffConfig{
		BaseDelay:  200 * time.Millisecond,
		Multiplier: 2.0,
		MaxDelay:   30 * time.Second,
		MaxRetries: 6,
		Jitter:     0.3,
	}

	for attempt := 0; attempt < cfg.MaxRetries; attempt++ {
		expDelay := float64(cfg.BaseDelay) * math.Pow(cfg.Multiplier, float64(attempt))
		minDelay := time.Duration(expDelay) // jitter >= 0
		maxDelay := time.Duration(expDelay * (1 + cfg.Jitter))

		// 多次采样验证范围
		for i := 0; i < 100; i++ {
			got := cfg.NextDelay(attempt)
			if got < minDelay || got > maxDelay {
				t.Errorf("attempt %d, 采样 %d: 延迟 %v 不在 [%v, %v] 范围内",
					attempt, i, got, minDelay, maxDelay)
			}
		}
	}
}

// TestNextDelayWithPressure 验证高压模式下延迟翻倍。
func TestNextDelayWithPressure(t *testing.T) {
	cfg := &BackoffConfig{
		BaseDelay:  200 * time.Millisecond,
		Multiplier: 2.0,
		MaxDelay:   60 * time.Second, // 足够大以避免钳制干扰
		MaxRetries: 6,
		Jitter:     0, // 关闭抖动
	}

	for attempt := 0; attempt < 3; attempt++ {
		normal := cfg.NextDelay(attempt)
		pressured := cfg.NextDelayWithPressure(attempt, true)

		if pressured != normal*2 {
			t.Errorf("attempt %d: 高压延迟 %v != 正常延迟 %v × 2", attempt, pressured, normal)
		}
	}

	// 非高压模式应等于正常值
	normal := cfg.NextDelay(0)
	nonPressured := cfg.NextDelayWithPressure(0, false)
	if normal != nonPressured {
		t.Errorf("非高压模式: %v != %v", nonPressured, normal)
	}
}

// TestNextDelayWithPressure_MaxRetriesExceeded 验证高压模式下超过重试次数返回 0。
func TestNextDelayWithPressure_MaxRetriesExceeded(t *testing.T) {
	cfg := DefaultConfig()
	got := cfg.NextDelayWithPressure(cfg.MaxRetries, true)
	if got != 0 {
		t.Errorf("超过最大重试次数后高压延迟 = %v, 期望 0", got)
	}
}

// TestShouldRetry 验证重试判断逻辑。
func TestShouldRetry(t *testing.T) {
	cfg := DefaultConfig()

	tests := []struct {
		attempt int
		want    bool
	}{
		{0, true},
		{3, true},
		{5, true},
		{6, false},  // == MaxRetries
		{10, false},
	}

	for _, tt := range tests {
		got := cfg.ShouldRetry(tt.attempt)
		if got != tt.want {
			t.Errorf("ShouldRetry(%d) = %v, 期望 %v", tt.attempt, got, tt.want)
		}
	}
}

// TestTotalMaxDuration 验证总最大耗时计算。
func TestTotalMaxDuration(t *testing.T) {
	cfg := &BackoffConfig{
		BaseDelay:  200 * time.Millisecond,
		Multiplier: 2.0,
		MaxDelay:   30 * time.Second,
		MaxRetries: 6,
		Jitter:     0.3,
	}

	total := cfg.TotalMaxDuration()

	// 手动计算：
	// attempt 0: 200ms * 1.3 = 260ms
	// attempt 1: 400ms * 1.3 = 520ms
	// attempt 2: 800ms * 1.3 = 1040ms
	// attempt 3: 1600ms * 1.3 = 2080ms
	// attempt 4: 3200ms * 1.3 = 4160ms
	// attempt 5: 6400ms * 1.3 = 8320ms
	// 总计: 16380ms ≈ 16.38s
	expected := 260 + 520 + 1040 + 2080 + 4160 + 8320
	expectedDuration := time.Duration(expected) * time.Millisecond

	if total != expectedDuration {
		t.Errorf("TotalMaxDuration = %v, 期望 %v", total, expectedDuration)
	}

	// 总耗时应远小于 MaxDelay * MaxRetries
	upperBound := cfg.MaxDelay * time.Duration(cfg.MaxRetries)
	if total > upperBound {
		t.Errorf("TotalMaxDuration %v 超过理论上限 %v", total, upperBound)
	}
}
