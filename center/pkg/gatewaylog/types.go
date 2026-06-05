// Package gatewaylog 定义网关流量日志数据结构。
package gatewaylog

// GatewayLog 网关流量日志条目。
type GatewayLog struct {
	URL            string `json:"url"`
	Method         string `json:"method"`
	StatusCode     int    `json:"status_code"`
	ResponseTimeMs int64  `json:"response_time_ms"`
	ClientIP       string `json:"client_ip"`
	Timestamp      int64  `json:"timestamp"`
	RequestSize    int64  `json:"request_size"`
	ResponseSize   int64  `json:"response_size"`
	ServiceName    string `json:"service_name"`
	UpstreamAddr   string `json:"upstream_addr"`
}
