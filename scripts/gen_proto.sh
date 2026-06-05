#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "[gen_proto] 生成 gRPC Go 代码..."
docker run --rm \
  -v "${ROOT}:/work" -w /work \
  golang:1.22-alpine sh -c '
    apk add --no-cache protobuf-dev protoc >/dev/null
    go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.34.1
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.4.0
    export PATH="$PATH:$(go env GOPATH)/bin"
    protoc -I proto \
      --go_out=proto --go_opt=module=github.com/p3-microservice/proto \
      --go-grpc_out=proto --go-grpc_opt=module=github.com/p3-microservice/proto \
      proto/log_service.proto proto/rule_service.proto
  '

docker run --rm -v "${ROOT}:/src" -w /src/proto golang:1.22-alpine go mod tidy
echo "[gen_proto] 完成: proto/logpb/"
