// Package matcher 实现定向规则匹配引擎。
//
// 职责：
// 1. 维护当前生效的关注清单（AttentionList）
// 2. 对每条日志进行规则匹配（URL/关键词/级别）
// 3. 支持热更新：运行时无锁切换规则集
// 4. 按权重排序，高优先级规则优先匹配
package matcher

import (
	"context"
	"log"
	"regexp"
	"sort"
	"strings"
	"sync/atomic"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
)

// Config 规则匹配器配置。
type Config struct {
	PullInterval   time.Duration // 关注清单拉取间隔
	MinLogLevel    string        // 默认最低日志级别
	CollectionMode string        // directed | full
}

// AttentionListItem 关注清单条目。
type AttentionListItem struct {
	Pattern     string   `json:"pattern"`      // URL 模式
	PatternType string   `json:"pattern_type"` // exact/prefix/regex/wildcard
	Weight      float64  `json:"weight"`       // 权重 (0.0-1.0)
	Reason      string   `json:"reason"`       // 关注原因
	Keywords    []string `json:"keywords"`     // 关键词过滤
	TTLSeconds  int64    `json:"ttl_seconds"`  // 有效期
	ExpiresAt   time.Time `json:"-"`           // 过期时间（运行时计算）

	compiledRegex *regexp.Regexp // 编译后的正则（缓存）
}

// AttentionList 关注清单。
type AttentionList struct {
	Version string              `json:"version"`
	Items   []AttentionListItem `json:"items"`
}

// RuleClient 用于从 Center 拉取规则的接口。
type RuleClient interface {
	PullAttentionList(agentID string, currentVersion string) (*AttentionList, error)
}

// RuleMatcher 定向规则匹配器。
type RuleMatcher struct {
	config       Config
	currentList  atomic.Value // 存储 *AttentionList
	minLogLevel  int
}

// NewRuleMatcher 创建规则匹配器。
func NewRuleMatcher(cfg Config) *RuleMatcher {
	rm := &RuleMatcher{
		config:      cfg,
		minLogLevel: parseLogLevel(cfg.MinLogLevel),
	}
	// 初始化空清单
	rm.currentList.Store(&AttentionList{
		Version: "",
		Items:   nil,
	})
	return rm
}

// Match 判断日志条目是否匹配当前关注清单中的任一规则。
// 返回 true 表示该日志应被采集。
func (m *RuleMatcher) Match(entry *cache.LogEntry) bool {
	if m.config.CollectionMode == "full" {
		return true
	}
	// 日志级别过滤（ERROR/FATAL 级别始终采集）
	entryLevel := parseLogLevel(entry.Level)
	if entryLevel >= logLevelError {
		return true
	}
	if entryLevel < m.minLogLevel {
		return false
	}

	list := m.currentList.Load().(*AttentionList)
	if list == nil || len(list.Items) == 0 {
		// 无关注清单时仅采集 ERROR+，避免退化为全量
		return entryLevel >= logLevelError
	}

	// 遍历清单（已按权重排序，高优先级优先匹配）
	for i := range list.Items {
		item := &list.Items[i]

		// 检查是否过期
		if !item.ExpiresAt.IsZero() && time.Now().After(item.ExpiresAt) {
			continue
		}

		// URL 模式匹配
		if m.matchPattern(entry.URL, item) {
			// 如果有关键词要求，还需匹配关键词
			if len(item.Keywords) > 0 {
				if m.matchKeywords(entry.Content, item.Keywords) {
					return true
				}
			} else {
				return true
			}
		}
	}

	return false
}

// matchPattern 根据模式类型匹配 URL。
func (m *RuleMatcher) matchPattern(url string, item *AttentionListItem) bool {
	if url == "" || item.Pattern == "" {
		return false
	}

	switch item.PatternType {
	case "exact":
		return url == item.Pattern

	case "prefix":
		return strings.HasPrefix(url, item.Pattern)

	case "regex":
		if item.compiledRegex == nil {
			compiled, err := regexp.Compile(item.Pattern)
			if err != nil {
				log.Printf("[Matcher] 正则编译失败: %s, err: %v", item.Pattern, err)
				return false
			}
			item.compiledRegex = compiled
		}
		return item.compiledRegex.MatchString(url)

	case "wildcard":
		return matchWildcard(url, item.Pattern)

	default:
		// 默认前缀匹配
		return strings.HasPrefix(url, item.Pattern)
	}
}

// matchKeywords 检查日志内容是否包含任一关键词。
func (m *RuleMatcher) matchKeywords(content string, keywords []string) bool {
	contentLower := strings.ToLower(content)
	for _, kw := range keywords {
		if strings.Contains(contentLower, strings.ToLower(kw)) {
			return true
		}
	}
	return false
}

// UpdateList 热更新关注清单（无锁切换）。
func (m *RuleMatcher) UpdateList(list *AttentionList) {
	if list == nil {
		return
	}

	// 按权重降序排序
	sort.Slice(list.Items, func(i, j int) bool {
		return list.Items[i].Weight > list.Items[j].Weight
	})

	// 计算过期时间
	now := time.Now()
	for i := range list.Items {
		if list.Items[i].TTLSeconds > 0 {
			list.Items[i].ExpiresAt = now.Add(time.Duration(list.Items[i].TTLSeconds) * time.Second)
		}
	}

	// 原子替换
	m.currentList.Store(list)
	log.Printf("[Matcher] 关注清单已更新: version=%s, items=%d", list.Version, len(list.Items))
}

// StartPulling 启动定时拉取关注清单。
func (m *RuleMatcher) StartPulling(ctx context.Context, client RuleClient) {
	ticker := time.NewTicker(m.config.PullInterval)
	defer ticker.Stop()

	currentVersion := ""

	for {
		select {
		case <-ctx.Done():
			log.Println("[Matcher] 停止规则拉取")
			return
		case <-ticker.C:
			list, err := client.PullAttentionList("", currentVersion)
			if err != nil {
				log.Printf("[Matcher] 拉取关注清单失败: %v", err)
				continue
			}
			if list != nil && list.Version != currentVersion {
				m.UpdateList(list)
				currentVersion = list.Version
			}
		}
	}
}

// GetCurrentList 返回当前关注清单的只读快照。
func (m *RuleMatcher) GetCurrentList() *AttentionList {
	return m.currentList.Load().(*AttentionList)
}

// ========================================
// 辅助函数
// ========================================

// 日志级别常量
const (
	logLevelDebug = 1
	logLevelInfo  = 2
	logLevelWarn  = 3
	logLevelError = 4
	logLevelFatal = 5
)

func parseLogLevel(level string) int {
	switch strings.ToUpper(level) {
	case "DEBUG":
		return logLevelDebug
	case "INFO":
		return logLevelInfo
	case "WARN", "WARNING":
		return logLevelWarn
	case "ERROR":
		return logLevelError
	case "FATAL":
		return logLevelFatal
	default:
		return logLevelInfo
	}
}

// matchWildcard 实现简单的通配符匹配（* 匹配任意字符序列）。
func matchWildcard(s, pattern string) bool {
	// 将通配符模式转为正则
	regexPattern := "^" + regexp.QuoteMeta(pattern) + "$"
	regexPattern = strings.ReplaceAll(regexPattern, `\*`, ".*")
	regexPattern = strings.ReplaceAll(regexPattern, `\?`, ".")

	matched, err := regexp.MatchString(regexPattern, s)
	if err != nil {
		return false
	}
	return matched
}
