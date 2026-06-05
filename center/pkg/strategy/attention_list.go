// Package strategy - 关注清单动态生成算法。
//
// 输入：高速缓存的网关流量日志 + 定向策略（超时阈值T等）
// 输出：关注清单（URL 模式 + 权重）
//
// 步骤：
// 1. 高价值过滤 → 筛选值得关注的流量记录
// 2. URL 聚类/泛化 → 合并相似 URL 为模式
// 3. 权重排序 + Top-K → 生成最终清单
// 4. 下发至各 Agent 节点
//
// 复杂度：O(N log N)（排序主导）
package strategy

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

// AttentionListConfig 关注清单生成器配置。
type AttentionListConfig struct {
	TopK       int               // Top-K URL 模式数量
	TTLSeconds int64             // 清单条目 TTL
	Filter     *HighValueFilter  // 高价值过滤器
	Clusterer  *URLClusterer     // URL 聚类器
}

// AttentionList 关注清单。
type AttentionList struct {
	Version   string              `json:"version"`
	Items     []AttentionListItem `json:"items"`
	ExpiresAt time.Time           `json:"expires_at"`
	Stats     GenerationStats     `json:"stats"`
}

// AttentionListItem 关注清单条目。
type AttentionListItem struct {
	Pattern     string   `json:"pattern"`      // URL 模式
	PatternType string   `json:"pattern_type"` // prefix / regex / wildcard
	Weight      float64  `json:"weight"`       // 权重 (0.0-1.0)
	Reason      string   `json:"reason"`       // 关注原因
	Keywords    []string `json:"keywords"`     // 关键词过滤
	TTLSeconds  int64    `json:"ttl_seconds"`  // 有效期
}

// GenerationStats 清单生成统计。
type GenerationStats struct {
	InputLogCount    int           `json:"input_log_count"`
	HighValueCount   int           `json:"high_value_count"`
	PatternCount     int           `json:"pattern_count"`
	FinalItemCount   int           `json:"final_item_count"`
	FilterRate       float64       `json:"filter_rate"`
	GenerationTimeMs int64         `json:"generation_time_ms"`
}

// AttentionListGenerator 关注清单生成器。
type AttentionListGenerator struct {
	config       AttentionListConfig
	currentList  atomic.Value // *AttentionList
	version      atomic.Int64
	mu           sync.Mutex
}

// NewAttentionListGenerator 创建关注清单生成器。
func NewAttentionListGenerator(cfg AttentionListConfig) *AttentionListGenerator {
	gen := &AttentionListGenerator{
		config: cfg,
	}
	// 初始化空清单
	gen.currentList.Store(&AttentionList{
		Version: "0",
		Items:   nil,
	})
	return gen
}

// Generate 基于网关流量日志生成关注清单。
//
// 这是定向采集清单动态生成算法的核心入口：
// Step 1: 高价值过滤 → 筛选慢请求/错误码/高错误率 URL
// Step 2: URL 聚类泛化 → 将具体 URL 合并为模式
// Step 3: Top-K 筛选 → 保留权重最高的 K 个模式
// Step 4: 构建清单 → 附加 TTL、模式类型等元信息
func (g *AttentionListGenerator) Generate(logs []GatewayLog) *AttentionList {
	g.mu.Lock()
	defer g.mu.Unlock()

	startTime := time.Now()

	// Step 1: 高价值过滤
	highValueLogs, filterStats := g.config.Filter.Filter(logs)
	log.Printf("[AttentionList] 高价值过滤: %d/%d 条 (过滤率 %.1f%%)",
		filterStats.HighValueCount, filterStats.TotalCount, filterStats.FilterRate*100)

	if len(highValueLogs) == 0 {
		log.Println("[AttentionList] 无高价值记录，清单为空")
		return g.buildEmptyList()
	}

	// Step 2: URL 聚类泛化
	patterns := g.config.Clusterer.Cluster(highValueLogs)
	log.Printf("[AttentionList] URL 聚类: 生成 %d 个模式", len(patterns))

	// Step 3: Top-K 筛选（Cluster 已按权重降序排列）
	topK := g.config.TopK
	if topK > len(patterns) {
		topK = len(patterns)
	}
	patterns = patterns[:topK]

	// Step 4: 构建清单
	items := make([]AttentionListItem, 0, len(patterns))
	for _, p := range patterns {
		items = append(items, AttentionListItem{
			Pattern:     p.Pattern,
			PatternType: detectPatternType(p.Pattern),
			Weight:      p.Weight,
			Reason:      p.Reason,
			Keywords:    nil,
			TTLSeconds:  g.config.TTLSeconds,
		})
	}

	// 更新版本号
	newVersion := g.version.Add(1)
	generationTime := time.Since(startTime)

	list := &AttentionList{
		Version:   fmt.Sprintf("v%d", newVersion),
		Items:     items,
		ExpiresAt: time.Now().Add(time.Duration(g.config.TTLSeconds) * time.Second),
		Stats: GenerationStats{
			InputLogCount:    len(logs),
			HighValueCount:   filterStats.HighValueCount,
			PatternCount:     len(patterns),
			FinalItemCount:   len(items),
			FilterRate:       filterStats.FilterRate,
			GenerationTimeMs: generationTime.Milliseconds(),
		},
	}

	// 原子更新当前清单
	g.currentList.Store(list)

	log.Printf("[AttentionList] 清单生成完成: version=%s, items=%d, 耗时=%v",
		list.Version, len(items), generationTime)

	return list
}

// GetCurrentList 获取当前关注清单。
func (g *AttentionListGenerator) GetCurrentList() *AttentionList {
	return g.currentList.Load().(*AttentionList)
}

// HTTPHandler 提供 HTTP API 查看当前关注清单。
func (g *AttentionListGenerator) HTTPHandler(w http.ResponseWriter, r *http.Request) {
	list := g.GetCurrentList()
	w.Header().Set("Content-Type", "application/json")

	data, err := json.MarshalIndent(list, "", "  ")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Write(data)
}

func (g *AttentionListGenerator) buildEmptyList() *AttentionList {
	newVersion := g.version.Add(1)
	list := &AttentionList{
		Version:   fmt.Sprintf("v%d", newVersion),
		Items:     nil,
		ExpiresAt: time.Now().Add(time.Duration(g.config.TTLSeconds) * time.Second),
	}
	g.currentList.Store(list)
	return list
}

// detectPatternType 根据模式内容推断匹配类型。
func detectPatternType(pattern string) string {
	// 包含 {id} / {uuid} 等占位符 → 需要正则匹配
	if containsPlaceholder(pattern) {
		return "regex"
	}
	// 包含 * 通配符
	if containsWildcard(pattern) {
		return "wildcard"
	}
	// 默认前缀匹配
	return "prefix"
}

func containsPlaceholder(s string) bool {
	inBrace := false
	for _, c := range s {
		if c == '{' {
			inBrace = true
		} else if c == '}' && inBrace {
			return true
		}
	}
	return false
}

func containsWildcard(s string) bool {
	for _, c := range s {
		if c == '*' || c == '?' {
			return true
		}
	}
	return false
}
