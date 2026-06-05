// Package strategy 实现定向策略的核心算法。
//
// 本文件实现高价值记录过滤器，是定向清单生成算法的第一步。
// 从网关流量日志中筛选出值得关注的记录（高延迟、错误码、高频等）。
package strategy

import "github.com/p3-microservice/center/pkg/gatewaylog"

// GatewayLog 网关流量日志（别名，兼容策略包引用）。
type GatewayLog = gatewaylog.GatewayLog

// HighValueFilterConfig 高价值过滤器配置。
type HighValueFilterConfig struct {
	ResponseTimeThresholdMs int64   // 响应时长阈值（毫秒）
	ErrorCodes              []int   // 关注的错误状态码
	ErrorRateThreshold      float64 // 错误率阈值
}

// HighValueFilter 高价值记录过滤器。
//
// 算法：从网关流量日志中识别以下高价值记录：
// 1. 响应时长超过阈值 T 的请求（慢请求）
// 2. 状态码在关注列表中的请求（错误请求）
// 3. 高频请求中错误率超过阈值的 URL（异常热点）
type HighValueFilter struct {
	config       HighValueFilterConfig
	errorCodeSet map[int]bool
}

// NewHighValueFilter 创建高价值过滤器。
func NewHighValueFilter(cfg HighValueFilterConfig) *HighValueFilter {
	codeSet := make(map[int]bool, len(cfg.ErrorCodes))
	for _, code := range cfg.ErrorCodes {
		codeSet[code] = true
	}
	return &HighValueFilter{
		config:       cfg,
		errorCodeSet: codeSet,
	}
}

// Filter 从网关日志中筛选高价值记录。
// 返回高价值日志列表和统计信息。
func (f *HighValueFilter) Filter(logs []GatewayLog) ([]GatewayLog, FilterStats) {
	stats := FilterStats{
		TotalCount: len(logs),
	}

	if len(logs) == 0 {
		return nil, stats
	}

	// 统计各 URL 的请求数和错误数（用于错误率计算）
	urlStats := make(map[string]*urlStat)
	for i := range logs {
		url := logs[i].URL
		us, ok := urlStats[url]
		if !ok {
			us = &urlStat{}
			urlStats[url] = us
		}
		us.total++
		if f.errorCodeSet[logs[i].StatusCode] {
			us.errors++
		}
	}

	// 计算各 URL 的错误率
	highErrorRateURLs := make(map[string]bool)
	for url, us := range urlStats {
		if us.total > 0 {
			errorRate := float64(us.errors) / float64(us.total)
			if errorRate >= f.config.ErrorRateThreshold && us.total >= 5 { // 至少 5 次请求才统计错误率
				highErrorRateURLs[url] = true
			}
		}
	}

	// 过滤高价值记录
	result := make([]GatewayLog, 0, len(logs)/4) // 预估 25% 为高价值
	seen := make(map[string]bool) // 去重

	for i := range logs {
		log := &logs[i]
		isHighValue := false
		reason := ""

		// 条件 1：慢请求
		if log.ResponseTimeMs >= f.config.ResponseTimeThresholdMs {
			isHighValue = true
			reason = "slow_request"
			stats.SlowRequestCount++
		}

		// 条件 2：错误码
		if f.errorCodeSet[log.StatusCode] {
			isHighValue = true
			reason = "error_code"
			stats.ErrorCodeCount++
		}

		// 条件 3：高错误率 URL
		if highErrorRateURLs[log.URL] {
			isHighValue = true
			if reason == "" {
				reason = "high_error_rate"
			}
			stats.HighErrorRateCount++
		}

		if isHighValue {
			key := log.URL + "|" + reason
			if !seen[key] { // 同一 URL + 原因去重
				seen[key] = true
			}
			result = append(result, *log)
		}
	}

	stats.HighValueCount = len(result)
	stats.FilterRate = 1.0 - float64(stats.HighValueCount)/float64(stats.TotalCount)

	return result, stats
}

// IsHighValue 判断单条日志是否为高价值。
func (f *HighValueFilter) IsHighValue(log *GatewayLog) bool {
	if log.ResponseTimeMs >= f.config.ResponseTimeThresholdMs {
		return true
	}
	if f.errorCodeSet[log.StatusCode] {
		return true
	}
	return false
}

// FilterStats 过滤统计信息。
type FilterStats struct {
	TotalCount        int     `json:"total_count"`
	HighValueCount    int     `json:"high_value_count"`
	SlowRequestCount  int     `json:"slow_request_count"`
	ErrorCodeCount    int     `json:"error_code_count"`
	HighErrorRateCount int    `json:"high_error_rate_count"`
	FilterRate        float64 `json:"filter_rate"` // 过滤比例（被过滤掉的占比）
}

type urlStat struct {
	total  int
	errors int
}
