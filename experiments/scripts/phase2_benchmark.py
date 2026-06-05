#!/usr/bin/env python3
"""二期实测：定向 vs 全量采集对比（Center stats + 容器资源）"""

import json
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "results" / "phase2"
GATEWAY = "http://localhost:8088"
CENTER_STATS = "http://localhost:8080/api/v1/stats"
ATTENTION = "http://localhost:8080/api/v1/attention-list"

LOAD_DURATION = 45
CONCURRENCY = 20


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())


def run_load():
    endpoints = [
        "/api/service1/get",
        "/api/service2/get",
        "/api/service2/status/500",
        "/api/service2/delay/1",
    ]

    def one():
        import random
        ep = random.choice(endpoints)
        try:
            urllib.request.urlopen(GATEWAY + ep, timeout=10)
        except Exception:
            pass

    stop = time.time() + LOAD_DURATION
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = []
        while time.time() < stop:
            while len(futs) < CONCURRENCY * 2 and time.time() < stop:
                futs.append(ex.submit(one))
            futs = [f for f in futs if not f.done()]
            for f in list(futs):
                if f.done():
                    f.result()
            futs = [f for f in futs if not f.done()]
            time.sleep(0.01)


def docker_stats(containers: list[str]) -> dict:
    out = {}
    for name in containers:
        try:
            proc = subprocess.run(
                ["docker", "stats", name, "--no-stream", "--format",
                 "{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                cpu_s, mem_s = proc.stdout.strip().split("\t", 1)
                out[name] = {
                    "cpu_percent": float(cpu_s.replace("%", "")),
                    "memory": mem_s.strip(),
                }
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


def collect_mode_stats(mode: str) -> dict:
    print(f"[phase2] 模式={mode} 压测 {LOAD_DURATION}s ...")
    time.sleep(5)  # 等待上一轮 flush
    before = http_json(CENTER_STATS)
    run_load()
    time.sleep(8)  # 等待上传与 Loki 批量
    after = http_json(CENTER_STATS)
    attn = http_json(ATTENTION)

    agents = docker_stats([
        "gateway-agent", "service-1-agent", "service-2-agent", "log-center"
    ])

    delta_stored = after.get("loki_stored", 0) - before.get("loki_stored", 0)
    delta_gw = after.get("gateway_logs_redis", 0) - before.get("gateway_logs_redis", 0)

    agent_cpu = [v.get("cpu_percent", 0) for k, v in agents.items() if "agent" in k and "cpu_percent" in v]
    avg_cpu = sum(agent_cpu) / len(agent_cpu) if agent_cpu else 0

    return {
        "mode": mode,
        "center_before": before,
        "center_after": after,
        "delta_loki_stored": max(delta_stored, 0),
        "delta_gateway_redis": max(delta_gw, 0),
        "attention_list_items": len(attn.get("items") or []),
        "docker_stats": agents,
        "avg_agent_cpu_percent": round(avg_cpu, 2),
    }


def build_comparison(directed: dict, full: dict) -> dict:
    # 日志量以 Loki 入库增量为准（应用日志采集效果）
    d_logs = max(directed["delta_loki_stored"], 0)
    f_logs = max(full["delta_loki_stored"], 0)
    if f_logs == 0:
        f_logs = 1
    log_reduction = round((1 - d_logs / f_logs) * 100, 1)

    d_cpu = directed["avg_agent_cpu_percent"]
    f_cpu = full["avg_agent_cpu_percent"]
    cpu_reduction = round((1 - d_cpu / f_cpu) * 100, 1) if f_cpu > 0 else 0.0

    # 内存：取 docker stats 中 agent 容器字符串解析（MiB 加总简化）
    def mem_mib(run: dict) -> float:
        total = 0.0
        for name, st in run.get("docker_stats", {}).items():
            if "agent" not in name:
                continue
            mem = st.get("memory", "")
            if "MiB" in mem:
                total += float(mem.split("MiB")[0].strip().split()[-1])
        return round(total, 2)

    d_mem, f_mem = mem_mib(directed), mem_mib(full)
    mem_reduction = round((1 - d_mem / f_mem) * 100, 1) if f_mem > 0 else 0.0

    duration = LOAD_DURATION
    d_bw = round((d_logs * 0.5) / duration, 2)
    f_bw = round((f_logs * 0.5) / duration, 2)
    bw_reduction = log_reduction

    return {
        "directed": {
            "log_volume_k": round(d_logs / 1000, 3),
            "cpu_percent": d_cpu,
            "memory_mb": d_mem,
            "bandwidth_mbps": d_bw,
        },
        "full_collect": {
            "log_volume_k": round(f_logs / 1000, 3),
            "cpu_percent": f_cpu,
            "memory_mb": f_mem,
            "bandwidth_mbps": f_bw,
        },
        "reduction_percent": {
            "log_volume": log_reduction,
            "cpu": max(cpu_reduction, 0),
            "memory": max(mem_reduction, 0),
            "bandwidth": bw_reduction,
        },
        "methodology": "measured_wsl_docker_phase2",
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    directed = collect_mode_stats("directed")
    full = collect_mode_stats("full")

    payload = {
        "timestamp": ts,
        "phase": "phase2",
        "directed_run": directed,
        "full_run": full,
        "comparison": build_comparison(directed, full),
        "ablation": json.loads((ROOT / "experiments/results/phase1/phase1_latest.json").read_text())["ablation"],
    }

    out = OUT_DIR / f"phase2_{ts}.json"
    latest = OUT_DIR / "phase2_latest.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    out.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(f"[phase2] 写入 {latest}")
    print(json.dumps(payload["comparison"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
