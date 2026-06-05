package grpcserver

import (
	"github.com/p3-microservice/center/pkg/dispatch"
	"github.com/p3-microservice/center/pkg/receiver"
	"github.com/p3-microservice/center/pkg/redisstore"
	"github.com/p3-microservice/center/pkg/strategy"
	"github.com/p3-microservice/proto/logpb"
	"google.golang.org/grpc"
)

// Config gRPC 服务配置。
type Config struct {
	LogReceiver *receiver.LogReceiver
	Dispatcher  *dispatch.RuleDispatcher
	ListGen     *strategy.AttentionListGenerator
}

// Server gRPC 服务门面。
type Server struct {
	upload *LogUploadServer
}

// NewServer 创建 gRPC 服务端。
func NewServer(cfg Config, gatewayStore *redisstore.GatewayLogStore) *Server {
	return &Server{
		upload: NewLogUploadServer(cfg, gatewayStore),
	}
}

// Register 注册 gRPC 服务。
func (s *Server) Register(srv *grpc.Server) {
	logpb.RegisterLogUploadServiceServer(srv, s.upload)
}
