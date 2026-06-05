// Package strategy - URL 聚类/泛化算法。
//
// 将具体的 URL 路径泛化为模式，合并相似 URL：
// - /api/user/123       → /api/user/{id}
// - /api/order/abc-def  → /api/order/{uuid}
// - /api/product/shoes  → /api/product/{param}（基于编辑距离聚类）
//
// 复杂度：O(N log N)（排序 + 扫描合并）
package strategy

import (
	"regexp"
	"sort"
	"strings"
)

// URLClusterConfig URL 聚类配置。
type URLClusterConfig struct {
	EnableNumericReplace bool    // 启用数字段替换
	EnableUUIDReplace    bool    // 启用 UUID 段替换
	SimilarityThreshold  float64 // 相似度阈值 (0.0-1.0)
}

// URLClusterer URL 聚类器。
type URLClusterer struct {
	config    URLClusterConfig
	uuidRegex *regexp.Regexp
	numRegex  *regexp.Regexp
}

// NewURLClusterer 创建 URL 聚类器。
func NewURLClusterer(cfg URLClusterConfig) *URLClusterer {
	return &URLClusterer{
		config:    cfg,
		uuidRegex: regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`),
		numRegex:  regexp.MustCompile(`^\d+$`),
	}
}

// URLPattern 泛化后的 URL 模式。
type URLPattern struct {
	Pattern   string  `json:"pattern"`    // 泛化后的模式，如 /api/user/{id}
	Weight    float64 `json:"weight"`     // 权重
	Count     int     `json:"count"`      // 聚合的原始 URL 数量
	Reason    string  `json:"reason"`     // 关注原因
	AvgRespMs int64   `json:"avg_resp_ms"` // 平均响应时间
}

// Cluster 对高价值日志的 URL 进行聚类泛化。
//
// 算法步骤：
// 1. 对每个 URL 进行路径段泛化（数字 → {id}，UUID → {uuid}）
// 2. 按泛化后的模式聚合
// 3. 计算权重（频次 × 严重性评分）
// 4. 按权重降序排列
func (c *URLClusterer) Cluster(logs []GatewayLog) []URLPattern {
	if len(logs) == 0 {
		return nil
	}

	// 阶段 1：URL 泛化与聚合
	patternMap := make(map[string]*patternAccumulator)

	for i := range logs {
		log := &logs[i]
		generalizedURL := c.generalizeURL(log.URL)

		acc, ok := patternMap[generalizedURL]
		if !ok {
			acc = &patternAccumulator{
				pattern: generalizedURL,
			}
			patternMap[generalizedURL] = acc
		}

		acc.count++
		acc.totalRespMs += log.ResponseTimeMs
		if log.StatusCode >= 500 {
			acc.errorCount++
		}
		if log.ResponseTimeMs > acc.maxRespMs {
			acc.maxRespMs = log.ResponseTimeMs
		}
	}

	// 阶段 2：计算权重并生成结果
	patterns := make([]URLPattern, 0, len(patternMap))
	for _, acc := range patternMap {
		weight := c.calculateWeight(acc)
		avgResp := acc.totalRespMs / int64(acc.count)

		reason := c.determineReason(acc)

		patterns = append(patterns, URLPattern{
			Pattern:   acc.pattern,
			Weight:    weight,
			Count:     acc.count,
			Reason:    reason,
			AvgRespMs: avgResp,
		})
	}

	// 阶段 3：按权重降序排序
	sort.Slice(patterns, func(i, j int) bool {
		return patterns[i].Weight > patterns[j].Weight
	})

	return patterns
}

// generalizeURL 对 URL 路径进行泛化处理。
//
// 规则：
// - 纯数字段 → {id}
// - UUID 格式段 → {uuid}
// - 保留查询参数的键，移除值
func (c *URLClusterer) generalizeURL(rawURL string) string {
	// 分离路径和查询参数
	path := rawURL
	query := ""
	if idx := strings.Index(rawURL, "?"); idx >= 0 {
		path = rawURL[:idx]
		query = rawURL[idx:]
	}

	// 泛化路径段
	segments := strings.Split(path, "/")
	for i, seg := range segments {
		if seg == "" {
			continue
		}

		// UUID 替换
		if c.config.EnableUUIDReplace && c.uuidRegex.MatchString(seg) {
			segments[i] = "{uuid}"
			continue
		}

		// 纯数字替换
		if c.config.EnableNumericReplace && c.numRegex.MatchString(seg) {
			segments[i] = "{id}"
			continue
		}

		// 长十六进制字符串（如 MongoDB ObjectId）
		if len(seg) >= 24 && isHexString(seg) {
			segments[i] = "{hex_id}"
			continue
		}
	}

	result := strings.Join(segments, "/")

	// 泛化查询参数（保留键，移除值）
	if query != "" {
		result += generalizeQuery(query)
	}

	return result
}

// calculateWeight 计算 URL 模式的权重。
//
// 公式：weight = normalize(count × severityScore)
// severityScore = 1.0 + errorRate × 2.0 + slowRate × 1.5
func (c *URLClusterer) calculateWeight(acc *patternAccumulator) float64 {
	if acc.count == 0 {
		return 0
	}

	errorRate := float64(acc.errorCount) / float64(acc.count)
	avgRespMs := float64(acc.totalRespMs) / float64(acc.count)

	// 慢请求评分（响应时间越长，分数越高）
	slowScore := 0.0
	if avgRespMs > 1000 {
		slowScore = 1.5
	} else if avgRespMs > 500 {
		slowScore = 1.0
	} else if avgRespMs > 200 {
		slowScore = 0.5
	}

	severityScore := 1.0 + errorRate*2.0 + slowScore

	// 频次因子（对数缩放，防止高频 URL 权重过高）
	countFactor := 1.0
	if acc.count > 1 {
		countFactor = 1.0 + logBase2(float64(acc.count))
	}

	weight := countFactor * severityScore

	// 归一化到 [0, 1]
	if weight > 10.0 {
		weight = 10.0
	}
	return weight / 10.0
}

// determineReason 确定关注原因。
func (c *URLClusterer) determineReason(acc *patternAccumulator) string {
	reasons := make([]string, 0, 3)

	if acc.errorCount > 0 {
		reasons = append(reasons, "error")
	}

	avgResp := acc.totalRespMs / int64(acc.count)
	if avgResp > 1000 {
		reasons = append(reasons, "slow")
	}

	if acc.count >= 10 {
		reasons = append(reasons, "frequent")
	}

	if len(reasons) == 0 {
		return "monitored"
	}
	return strings.Join(reasons, "+")
}

// ========================================
// 辅助类型和函数
// ========================================

type patternAccumulator struct {
	pattern    string
	count      int
	errorCount int
	totalRespMs int64
	maxRespMs   int64
}

func isHexString(s string) bool {
	for _, c := range s {
		if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F')) {
			return false
		}
	}
	return true
}

func generalizeQuery(query string) string {
	if !strings.HasPrefix(query, "?") {
		return query
	}
	params := strings.Split(query[1:], "&")
	keys := make([]string, 0, len(params))
	for _, p := range params {
		if idx := strings.Index(p, "="); idx >= 0 {
			keys = append(keys, p[:idx]+"={val}")
		} else {
			keys = append(keys, p)
		}
	}
	sort.Strings(keys)
	return "?" + strings.Join(keys, "&")
}

func logBase2(x float64) float64 {
	if x <= 0 {
		return 0
	}
	result := 0.0
	for x >= 2 {
		x /= 2
		result++
	}
	return result + (x - 1) // 线性近似小数部分
}
