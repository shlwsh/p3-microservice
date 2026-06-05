// Package metrics 提供 Prometheus 指标采集。
package metrics

import (
	"fmt"
	"log"
	"net/http"
)

// StartServer 启动 Prometheus 指标 HTTP 服务。
func StartServer(port int, path string) {
	go func() {
		mux := http.NewServeMux()
		mux.HandleFunc(path, func(w http.ResponseWriter, r *http.Request) {
			// TODO: 集成 prometheus/client_golang
			// promhttp.Handler().ServeHTTP(w, r)
			w.Header().Set("Content-Type", "text/plain")
			fmt.Fprintln(w, "# HELP agent_cache_entries Current number of cached log entries")
			fmt.Fprintln(w, "# TYPE agent_cache_entries gauge")
			fmt.Fprintln(w, "agent_cache_entries 0")
			fmt.Fprintln(w, "# HELP agent_retry_total Total number of retry attempts")
			fmt.Fprintln(w, "# TYPE agent_retry_total counter")
			fmt.Fprintln(w, "agent_retry_total 0")
			fmt.Fprintln(w, "# HELP agent_upload_success_total Total successful uploads")
			fmt.Fprintln(w, "# TYPE agent_upload_success_total counter")
			fmt.Fprintln(w, "agent_upload_success_total 0")
			fmt.Fprintln(w, "# HELP agent_dropped_total Total dropped log entries")
			fmt.Fprintln(w, "# TYPE agent_dropped_total counter")
			fmt.Fprintln(w, "agent_dropped_total 0")
		})

		addr := fmt.Sprintf(":%d", port)
		log.Printf("[Metrics] Prometheus 指标服务启动在 %s%s", addr, path)
		if err := http.ListenAndServe(addr, mux); err != nil {
			log.Printf("[Metrics] 指标服务启动失败: %v", err)
		}
	}()
}
