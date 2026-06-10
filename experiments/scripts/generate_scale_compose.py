#!/usr/bin/env python3
"""生成 N 节点规模的 Docker Compose 与 Nginx 路由配置（N=8/16/32/64）。"""

import argparse
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKER_DIR = ROOT / "deploy" / "docker"
NGINX_DIR = ROOT / "deploy" / "nginx"


def service_block(i: int) -> str:
    return f"""  service-{i}:
    image: kennethreitz/httpbin:latest
    container_name: service-{i}
    networks:
      - lognet

  service-{i}-agent:
    build:
      context: ../../
      dockerfile: deploy/docker/Dockerfile.agent
    container_name: service-{i}-agent
    environment:
      - AGENT_CONFIG_PATH=/etc/agent/agent.yaml
    volumes:
      - ./agents/service-{i}-agent.yaml:/etc/agent/agent.yaml
    depends_on:
      - center
    network_mode: "service:service-{i}"
"""


def wsl_agent_limits(i: int) -> str:
    return f"  service-{i}-agent:\n    mem_limit: 96m\n"


def generate_compose(n: int) -> str:
    # 基础 compose 已有 service-1/2；scale 从 3 起；本生成器覆盖 3..N
    start = 3 if n > 2 else 1
    blocks = [service_block(i) for i in range(start, n + 1)]
    header = f"""# 自动生成：{n} 微服务节点（叠加 docker-compose.yml 使用）
# 生成：python3 experiments/scripts/generate_scale_compose.py --nodes {n}
version: '3.8'

services:
"""
    return header + "\n".join(blocks)


def generate_wsl_limits(n: int) -> str:
    lines = [
        "# 自动生成 WSL 内存限制",
        "version: '3.8'",
        "",
        "services:",
    ]
    for i in range(1, n + 1):
        lines.append(f"  service-{i}-agent:")
        lines.append("    mem_limit: 96m")
    return "\n".join(lines) + "\n"


def generate_nginx(n: int) -> str:
    upstreams = "\n".join(
        f"    upstream service_{i} {{\n        server service-{i}:80;\n    }}"
        for i in range(1, n + 1)
    )
    locations = "\n".join(
        textwrap.dedent(f"""\
        location /api/service{i}/ {{
            proxy_pass http://service_{i}/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            log_by_lua_file /usr/local/openresty/nginx/lua/log_capture.lua;
        }}""")
        for i in range(1, n + 1)
    )
    return textwrap.dedent(f"""\
        # Nginx 配置 - 网关节点（{n} 服务路由，自动生成）
        worker_processes auto;
        error_log /dev/stderr warn;

        events {{
            worker_connections 4096;
            use epoll;
            multi_accept on;
        }}

        http {{
            include       mime.types;
            default_type  application/octet-stream;

            log_format main '$remote_addr - $remote_user [$time_local] '
                            '"$request" $status $body_bytes_sent '
                            '"$http_referer" "$http_user_agent" '
                            'rt=$request_time uct=$upstream_connect_time '
                            'urt=$upstream_response_time';

            access_log /dev/stdout main;
            sendfile on;
            tcp_nopush on;
            tcp_nodelay on;
            keepalive_timeout 65;

            lua_shared_dict log_buffer 32m;
            lua_package_path "/usr/local/openresty/nginx/lua/?.lua;;";

        {upstreams}

            server {{
                listen 80;
                server_name _;

                location = /_agent/logs {{
                    allow 127.0.0.1;
                    deny all;
                    content_by_lua_file /usr/local/openresty/nginx/lua/log_pull.lua;
                }}

                location /health {{
                    return 200 '{{"status":"ok","component":"gateway"}}';
                    add_header Content-Type application/json;
                }}

        {locations}

                location / {{
                    return 404 '{{"error":"not_found"}}';
                    add_header Content-Type application/json;
                }}
            }}
        }}
    """)


def generate_agent_configs(n: int) -> None:
    template = (DOCKER_DIR / "service-agent-config.yaml").read_text(encoding="utf-8")
    agents_dir = DOCKER_DIR / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        cfg = (
            template.replace('agent_id: "service-agent"', f'agent_id: "service-{i}-agent"')
            .replace('service_name: "httpbin"', f'service_name: "service-{i}"')
        )
        (agents_dir / f"service-{i}-agent.yaml").write_text(cfg, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, required=True, choices=[8, 16, 32, 64])
    args = ap.parse_args()
    n = args.nodes

    scale_path = DOCKER_DIR / f"docker-compose.scale{n}.yml"
    wsl_path = DOCKER_DIR / f"docker-compose.wsl{n}.yml"
    nginx_path = NGINX_DIR / f"nginx.scale{n}.conf"

    if n <= 8:
        # 8 节点沿用已有 scale.yml（service 3-8）
        scale_content = generate_compose(8)
    else:
        scale_content = generate_compose(n)

    scale_path.write_text(scale_content, encoding="utf-8")
    wsl_path.write_text(generate_wsl_limits(n), encoding="utf-8")
    nginx_path.write_text(generate_nginx(n), encoding="utf-8")
    generate_agent_configs(n)

    print(f"generated: {scale_path}")
    print(f"generated: {wsl_path}")
    print(f"generated: {nginx_path}")
    print(f"agent configs: 1..{n}")


if __name__ == "__main__":
    main()
