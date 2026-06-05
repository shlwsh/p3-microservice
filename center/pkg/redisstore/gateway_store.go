// Package redisstore 将网关流量日志写入 Redis，供关注清单生成读取。
package redisstore

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/p3-microservice/center/pkg/gatewaylog"
	"github.com/redis/go-redis/v9"
)

const defaultListKey = "gateway:traffic:logs"

// GatewayLogStore Redis 网关流量日志存储。
type GatewayLogStore struct {
	client *redis.Client
	key    string
}

// NewGatewayLogStore 创建网关日志存储。
func NewGatewayLogStore(addr, password string, db int) (*GatewayLogStore, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("redis ping: %w", err)
	}
	return &GatewayLogStore{client: client, key: defaultListKey}, nil
}

// Append 追加一条网关流量日志。
func (s *GatewayLogStore) Append(ctx context.Context, log gatewaylog.GatewayLog) error {
	data, err := json.Marshal(log)
	if err != nil {
		return err
	}
	if err := s.client.RPush(ctx, s.key, data).Err(); err != nil {
		return err
	}
	// 保留最近 100k 条，防止无限增长
	s.client.LTrim(ctx, s.key, -100000, -1)
	return nil
}

// AppendBatch 批量追加。
func (s *GatewayLogStore) AppendBatch(ctx context.Context, logs []gatewaylog.GatewayLog) error {
	if len(logs) == 0 {
		return nil
	}
	pipe := s.client.Pipeline()
	for _, log := range logs {
		data, err := json.Marshal(log)
		if err != nil {
			return err
		}
		pipe.RPush(ctx, s.key, data)
	}
	pipe.LTrim(ctx, s.key, -100000, -1)
	_, err := pipe.Exec(ctx)
	return err
}

// FetchWindow 读取时间窗口内的日志（毫秒时间戳）。
func (s *GatewayLogStore) FetchWindow(ctx context.Context, windowSec int64) ([]gatewaylog.GatewayLog, error) {
	raw, err := s.client.LRange(ctx, s.key, 0, -1).Result()
	if err != nil {
		return nil, err
	}
	cutoff := time.Now().Add(-time.Duration(windowSec) * time.Second).UnixMilli()
	out := make([]gatewaylog.GatewayLog, 0, len(raw))
	for _, item := range raw {
		var log gatewaylog.GatewayLog
		if err := json.Unmarshal([]byte(item), &log); err != nil {
			continue
		}
		if log.Timestamp == 0 || log.Timestamp >= cutoff {
			out = append(out, log)
		}
	}
	return out, nil
}

// Count 返回当前列表长度。
func (s *GatewayLogStore) Count(ctx context.Context) (int64, error) {
	return s.client.LLen(ctx, s.key).Result()
}

// Close 关闭连接。
func (s *GatewayLogStore) Close() error {
	return s.client.Close()
}
