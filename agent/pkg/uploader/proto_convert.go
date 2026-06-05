package uploader

import (
	"fmt"
	"time"

	"github.com/p3-microservice/agent/pkg/cache"
	"github.com/p3-microservice/proto/logpb"
	"google.golang.org/protobuf/types/known/timestamppb"
)

func entriesToProto(batch []*cache.LogEntry, agentID string) []*logpb.LogEntry {
	out := make([]*logpb.LogEntry, 0, len(batch))
	for _, e := range batch {
		out = append(out, entryToProto(e, agentID))
	}
	return out
}

func entryToProto(e *cache.LogEntry, agentID string) *logpb.LogEntry {
	ts := e.Timestamp
	if ts.IsZero() {
		ts = time.Now()
	}
	instanceID := e.InstanceID
	if instanceID == "" {
		instanceID = agentID
	}
	return &logpb.LogEntry{
		LogId:          firstNonEmpty(e.LogID, fmt.Sprintf("%s-%d", agentID, ts.UnixNano())),
		ServiceName:    e.ServiceName,
		InstanceId:     instanceID,
		Timestamp:      timestamppb.New(ts),
		Level:          stringToLogLevel(e.Level),
		Url:            e.URL,
		Method:         e.Method,
		StatusCode:     int32(e.StatusCode),
		ResponseTimeMs: e.ResponseTimeMs,
		TraceId:        e.TraceID,
		SpanId:         e.SpanID,
		Content:        e.Content,
		ClientIp:       e.ClientIP,
		Source:         stringToLogSource(e.Source),
		Metadata:       e.Metadata,
	}
}

func stringToLogLevel(level string) logpb.LogLevel {
	switch level {
	case "DEBUG":
		return logpb.LogLevel_DEBUG
	case "INFO":
		return logpb.LogLevel_INFO
	case "WARN":
		return logpb.LogLevel_WARN
	case "ERROR":
		return logpb.LogLevel_ERROR
	case "FATAL":
		return logpb.LogLevel_FATAL
	default:
		return logpb.LogLevel_INFO
	}
}

func stringToLogSource(source string) logpb.LogSource {
	switch source {
	case "GATEWAY":
		return logpb.LogSource_GATEWAY
	case "APPLICATION":
		return logpb.LogSource_APPLICATION
	default:
		return logpb.LogSource_SYSTEM
	}
}

func protoToAttentionList(resp *logpb.PullAttentionListResponse) *attentionListFromProto {
	if resp == nil || len(resp.GetItems()) == 0 {
		return nil
	}
	items := make([]attentionItemFromProto, 0, len(resp.GetItems()))
	for _, it := range resp.GetItems() {
		items = append(items, attentionItemFromProto{
			Pattern:     it.GetPattern(),
			PatternType: patternTypeFromProto(it.GetPatternType()),
			Weight:      it.GetWeight(),
			Reason:      it.GetReason(),
			Keywords:    it.GetKeywords(),
			TTLSeconds:  it.GetTtlSeconds(),
		})
	}
	return &attentionListFromProto{
		Version: resp.GetVersion(),
		Items:   items,
	}
}

type attentionListFromProto struct {
	Version string
	Items   []attentionItemFromProto
}

type attentionItemFromProto struct {
	Pattern     string
	PatternType string
	Weight      float64
	Reason      string
	Keywords    []string
	TTLSeconds  int64
}

func patternTypeFromProto(t logpb.PatternType) string {
	switch t {
	case logpb.PatternType_EXACT:
		return "exact"
	case logpb.PatternType_PREFIX:
		return "prefix"
	case logpb.PatternType_REGEX:
		return "regex"
	case logpb.PatternType_WILDCARD:
		return "wildcard"
	default:
		return "prefix"
	}
}

func firstNonEmpty(a, b string) string {
	if a != "" {
		return a
	}
	return b
}
