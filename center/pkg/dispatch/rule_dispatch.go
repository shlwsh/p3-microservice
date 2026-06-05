// Package dispatch 实现规则下发管理。
//
// 负责：
// 1. 管理所有在线 Agent 节点的注册与心跳
// 2. 将关注清单/过滤规则广播到所有 Agent
// 3. 跟踪各节点的规则版本一致性
package dispatch

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"
)

// AgentInfo 在线 Agent 节点信息。
type AgentInfo struct {
	AgentID         string    `json:"agent_id"`
	ServiceName     string    `json:"service_name"`
	Address         string    `json:"address"`
	LastHeartbeat   time.Time `json:"last_heartbeat"`
	CurrentRuleVer  string    `json:"current_rule_version"`
	CPUUsage        float64   `json:"cpu_usage"`
	MemoryUsage     float64   `json:"memory_usage"`
	Online          bool      `json:"online"`
}

// RuleDispatcher 规则下发管理器。
type RuleDispatcher struct {
	agents   map[string]*AgentInfo
	mu       sync.RWMutex

	// 最新的规则版本
	latestRuleVersion string
	latestRule        interface{} // *strategy.AgentFilterRule
}

// NewRuleDispatcher 创建规则下发管理器。
func NewRuleDispatcher() *RuleDispatcher {
	return &RuleDispatcher{
		agents: make(map[string]*AgentInfo),
	}
}

// RegisterAgent 注册/更新 Agent 节点。
func (d *RuleDispatcher) RegisterAgent(agentID string, info *AgentInfo) {
	d.mu.Lock()
	defer d.mu.Unlock()

	info.Online = true
	info.LastHeartbeat = time.Now()
	d.agents[agentID] = info

	log.Printf("[Dispatcher] Agent 注册: id=%s, service=%s", agentID, info.ServiceName)
}

// Heartbeat 处理 Agent 心跳。
func (d *RuleDispatcher) Heartbeat(agentID string, cpuUsage, memUsage float64) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	agent, ok := d.agents[agentID]
	if !ok {
		// 未注册的 Agent，忽略
		return false
	}

	agent.LastHeartbeat = time.Now()
	agent.CPUUsage = cpuUsage
	agent.MemoryUsage = memUsage
	agent.Online = true

	// 检查是否需要更新规则
	needUpdate := agent.CurrentRuleVer != d.latestRuleVersion
	return needUpdate
}

// BroadcastRules 将规则广播到所有在线 Agent。
func (d *RuleDispatcher) BroadcastRules(rule interface{}) {
	d.mu.Lock()
	d.latestRule = rule
	// 从规则中提取版本号（简化处理）
	d.latestRuleVersion = time.Now().Format("20060102150405")
	d.mu.Unlock()

	d.mu.RLock()
	defer d.mu.RUnlock()

	onlineCount := 0
	for _, agent := range d.agents {
		if agent.Online {
			onlineCount++
			// TODO: 通过 gRPC 推送或标记需要更新
			// 实际实现中，Agent 通过 PullAttentionList 主动拉取
		}
	}

	log.Printf("[Dispatcher] 规则广播: version=%s, online_agents=%d",
		d.latestRuleVersion, onlineCount)
}

// GetOnlineAgents 返回所有在线 Agent 列表。
func (d *RuleDispatcher) GetOnlineAgents() []*AgentInfo {
	d.mu.RLock()
	defer d.mu.RUnlock()

	result := make([]*AgentInfo, 0, len(d.agents))
	for _, agent := range d.agents {
		if agent.Online {
			result = append(result, agent)
		}
	}
	return result
}

// CheckAlive 检查并标记超时的 Agent 为离线。
func (d *RuleDispatcher) CheckAlive(timeout time.Duration) {
	d.mu.Lock()
	defer d.mu.Unlock()

	now := time.Now()
	for id, agent := range d.agents {
		if agent.Online && now.Sub(agent.LastHeartbeat) > timeout {
			agent.Online = false
			log.Printf("[Dispatcher] Agent 离线: id=%s (超时 %v)", id, timeout)
		}
	}
}

// HTTPAgentListHandler 提供 HTTP API 查看 Agent 列表。
func (d *RuleDispatcher) HTTPAgentListHandler(w http.ResponseWriter, r *http.Request) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	data, _ := json.MarshalIndent(d.agents, "", "  ")
	w.Write(data)
}
