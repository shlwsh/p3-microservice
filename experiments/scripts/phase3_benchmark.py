#!/usr/bin/env python3
"""三期实测：8 节点、真实风格应用日志、180s 长压测、3 次重复"""

import json
import statistics
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "experiments" / "results" / "phase3"
GATEWAY = "http://localhost:8088"
CENTER_STATS = "http://localhost:8080/api/v1/stats"
ATTENTION = "http://localhost:8080/api/v1/attention-list"

LOAD_DURATION = 180
CONCURRENCY = 50
REPEATS = 3
WARMUP_SEC = 30

AGENT_CONTAINERS = [
    "gateway-agent",
    *[f"service-{i}-agent" for i in range(1, 9)],
]


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())


def build_endpoints() -> list[str]:
    eps = []
    for i in range(1, 9):
        base = f"/api/service{i}"
        eps.extend([
            f"{base}/get",
            f"{base}/headers",
            f"{base}/status/500",
            f"{base}/delay/1",
        ])
    return eps


ENDPOINTS = build_endpoints()


def run_load(duration: int = LOAD_DURATION):
    import random

    def one():
        ep = random.choice(ENDPOINTS)
        try:
            urllib.request.urlopen(GATEWAY + ep, timeout=15)
        except Exception:
            pass

    stop = time.time() + duration
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = []
        while time.time() < stop:
            while len(futs) < CONCURRENCY * 3 and time.time() < stop:
                futs.append(ex.submit(one))
            for f in list(futs):
                if f.done():
                    try:
                        f.result()
                    except Exception:
                        pass
            futs = [f for f in futs if not f.done()]
            time.sleep(0.005)


def wait_attention(min_items: int = 1, timeout: int = 90) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            attn = http_json(ATTENTION)
            items = attn.get("items") or []
            if len(items) >= min_items:
                return attn
        except Exception:
            pass
        time.sleep(3)
    return http_json(ATTENTION)


def docker_stats(containers: list[str]) -> dict:
    out = {}
    for name in containers:
        try:
            proc = subprocess.run(
                ["docker", "stats", name, "--no-stream", "--format",
                 "{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True, text=True, timeout=15,
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


def mem_mib(run: dict) -> float:
    total = 0.0
    for name, st in run.get("docker_stats", {}).items():
        if "agent" not in name:
            continue
        mem = st.get("memory", "")
        if "MiB" in mem:
            total += float(mem.split("MiB")[0].strip().split()[-1])
    return round(total, 2)


def collect_one_run(mode: str, run_idx: int) -> dict:
    print(f"[phase3] mode={mode} repeat={run_idx+1}/{REPEATS} load={LOAD_DURATION}s ...")
    time.sleep(5)
    if mode == "directed":
        wait_attention(min_items=1, timeout=60)
    before = http_json(CENTER_STATS)
    run_load()
    time.sleep(12)
    after = http_json(CENTER_STATS)
    attn = http_json(ATTENTION)
    agents = docker_stats(AGENT_CONTAINERS)

    delta_stored = max(after.get("loki_stored", 0) - before.get("loki_stored", 0), 0)
    delta_gw = max(after.get("gateway_logs_redis", 0) - before.get("gateway_logs_redis", 0), 0)
    agent_cpu = [v.get("cpu_percent", 0) for v in agents.values() if "cpu_percent" in v]

    return {
        "mode": mode,
        "repeat": run_idx + 1,
        "delta_loki_stored": delta_stored,
        "delta_gateway_redis": delta_gw,
        "attention_list_items": len(attn.get("items") or []),
        "docker_stats": agents,
        "avg_agent_cpu_percent": round(sum(agent_cpu) / len(agent_cpu), 2) if agent_cpu else 0,
        "total_agent_memory_mb": mem_mib({"docker_stats": agents}),
    }


def aggregate_runs(runs: list[dict]) -> dict:
    logs = [r["delta_loki_stored"] for r in runs]
    cpus = [r["avg_agent_cpu_percent"] for r in runs]
    mems = [r["total_agent_memory_mb"] for r in runs]
    return {
        "runs": runs,
        "loki_stored_mean": round(statistics.mean(logs), 1),
        "loki_stored_stdev": round(statistics.stdev(logs), 1) if len(logs) > 1 else 0.0,
        "cpu_mean": round(statistics.mean(cpus), 2),
        "cpu_stdev": round(statistics.stdev(cpus), 2) if len(cpus) > 1 else 0.0,
        "memory_mb_mean": round(statistics.mean(mems), 2),
        "memory_mb_stdev": round(statistics.stdev(mems), 2) if len(mems) > 1 else 0.0,
    }


def build_comparison(directed: dict, full: dict) -> dict:
    d_logs = directed["loki_stored_mean"]
    f_logs = full["loki_stored_mean"] or 1
    log_reduction = round((1 - d_logs / f_logs) * 100, 1)

    d_cpu, f_cpu = directed["cpu_mean"], full["cpu_mean"]
    cpu_reduction = round((1 - d_cpu / f_cpu) * 100, 1) if f_cpu > 0 else 0.0

    d_mem, f_mem = directed["memory_mb_mean"], full["memory_mb_mean"]
    mem_reduction = round((1 - d_mem / f_mem) * 100, 1) if f_mem > 0 else 0.0

    duration = LOAD_DURATION
    return {
        "directed": {
            "log_volume_k": round(d_logs / 1000, 3),
            "log_volume_stdev": directed["loki_stored_stdev"],
            "cpu_percent": d_cpu,
            "cpu_stdev": directed["cpu_stdev"],
            "memory_mb": d_mem,
            "memory_stdev": directed["memory_mb_stdev"],
            "bandwidth_mbps": round((d_logs * 0.5) / duration, 2),
        },
        "full_collect": {
            "log_volume_k": round(f_logs / 1000, 3),
            "log_volume_stdev": full["loki_stored_stdev"],
            "cpu_percent": f_cpu,
            "cpu_stdev": full["cpu_stdev"],
            "memory_mb": f_mem,
            "memory_stdev": full["memory_mb_stdev"],
            "bandwidth_mbps": round((f_logs * 0.5) / duration, 2),
        },
        "reduction_percent": {
            "log_volume": log_reduction,
            "cpu": max(cpu_reduction, 0),
            "memory": max(mem_reduction, 0),
            "bandwidth": log_reduction,
        },
        "methodology": "measured_wsl_docker_phase3_8nodes_180s_x3",
        "nodes": 8,
        "load_duration_sec": LOAD_DURATION,
        "concurrency": CONCURRENCY,
        "repeats": REPEATS,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"[phase3] warmup {WARMUP_SEC}s ...")
    run_load(WARMUP_SEC)
    wait_attention()

    directed_runs = [collect_one_run("directed", i) for i in range(REPEATS)]
    full_runs = [collect_one_run("full", i) for i in range(REPEATS)]

    directed_agg = aggregate_runs(directed_runs)
    full_agg = aggregate_runs(full_runs)

    payload = {
        "timestamp": ts,
        "phase": "phase3",
        "directed": directed_agg,
        "full": full_agg,
        "comparison": build_comparison(directed_agg, full_agg),
    }

    out = OUT_DIR / f"phase3_{ts}.json"
    latest = OUT_DIR / "phase3_latest.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    out.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(f"[phase3] wrote {latest}")
    print(json.dumps(payload["comparison"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
