"""Playwright Chrome session with proxy lock for institutional SSO."""

from __future__ import annotations

import json
import os
from pathlib import Path

from download_lib import DEFAULT_PROXY, resolve_proxy

ROOT = Path(__file__).resolve().parent


def _proxy_host_port(proxy_server: str) -> str:
    return proxy_server.replace("http://", "").replace("https://", "")


def proxy_server_url() -> str:
    return os.environ.get("SCHOLAR_PROXY") or (resolve_proxy() or {}).get("http") or DEFAULT_PROXY


def build_launch_options(user_data_dir: str, proxy_server: str) -> dict:
    host_port = _proxy_host_port(proxy_server)
    chrome_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-features=BounceTrackingMitigations",
        f"--proxy-server={host_port}",
        "--proxy-pac-url=",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    return {
        "user_data_dir": user_data_dir,
        "headless": False,
        "args": chrome_args,
        "proxy": {
            "server": proxy_server,
            "bypass": "localhost;127.0.0.1;*.local;<local>",
        },
    }


def fix_chrome_profile_proxy(user_data_dir: str, proxy_server: str) -> None:
    prefs_path = os.path.join(user_data_dir, "Default", "Preferences")
    if not os.path.isfile(prefs_path):
        return
    host_port = _proxy_host_port(proxy_server)
    with open(prefs_path, encoding="utf-8") as f:
        prefs = json.load(f)
    prefs["proxy"] = {"mode": "fixed_servers", "server": host_port}
    for key in ("pac_url", "pac_mandatory", "bypass_list"):
        prefs["proxy"].pop(key, None)
    with open(prefs_path, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, separators=(",", ":"))


def verify_network(page, label: str) -> bool:
    test_url = "https://www.baidu.com"
    print(f"[进展] 网络自检（{label}）：{test_url}")
    try:
        response = page.goto(test_url, wait_until="domcontentloaded", timeout=20000)
        ok = response is not None and response.ok
        print(f"[进展] {'✅' if ok else '❌'} {label}")
        return ok
    except Exception as e:
        print(f"[进展] ❌ {label}: {e}")
        return False


def print_login_guide() -> None:
    print("\n" + "=" * 64)
    print("📌 西北大学 CARSI / 机构登录（推荐）")
    print("   1. 打开 ieee.org → Institutional Sign In → Northwest University")
    print("   2. 用信息门户账号登录 authserver.nwu.edu.cn")
    print("   3. 或配置 config/library_credentials.json 后设 AUTO_LOGIN=1")
    print("❌ 勿在 lib.nwu.edu.cn 启用超星「校外访问」全局代理")
    print("   CARSI 说明: https://app.nwu.edu.cn/wap/material?id=2688")
    print("=" * 64 + "\n")
