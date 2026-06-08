#!/usr/bin/env python3
"""CLI: OA/Sci-Hub first, then NWU CARSI/IEEE institutional login for remaining PDFs."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("no_proxy", "*")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from browser_session import (  # noqa: E402
    build_launch_options,
    fix_chrome_profile_proxy,
    print_login_guide,
    proxy_server_url,
    verify_network,
)
from download_lib import (  # noqa: E402
    DEFAULT_OUTPUT,
    dest_path_for,
    download_batch,
    download_paper,
    format_results_summary,
    is_valid_pdf,
    load_paper_config,
    write_manifest,
)
from library_auth import CREDENTIALS_PATH, ensure_publisher_login  # noqa: E402

OUTPUT_DIR = Path(os.environ.get("PAPER1_OUTPUT", str(DEFAULT_OUTPUT)))
USER_DATA_DIR = os.path.abspath(str(ROOT / "chrome_profile"))
SKIP_LOGIN = os.environ.get("SKIP_LOGIN", "").lower() in ("1", "true", "yes")
USE_SCIHUB = os.environ.get("USE_SCIHUB", "1").lower() not in ("0", "false", "no")
AUTO_LOGIN = os.environ.get("AUTO_LOGIN", "1" if CREDENTIALS_PATH.is_file() else "0").lower() in (
    "1",
    "true",
    "yes",
)


def _publisher_for_doi(doi: str) -> str:
    if doi.startswith("10.1109/"):
        return "ieee"
    if doi.startswith("10.1007/"):
        return "springer"
    if doi.startswith("10.1016/"):
        return "elsevier"
    return "ieee"


def main() -> int:
    papers = load_paper_config()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    proxy = proxy_server_url()

    # Only download items not yet on disk
    need = [p for p in papers if not is_valid_pdf(dest_path_for(OUTPUT_DIR, p))]
    if not need:
        print("全部 PDF 已存在，无需下载。")
        return 0

    print(f"输出目录: {OUTPUT_DIR}")
    print(f"待下载: {len(need)} 篇")
    print(f"阶段 1/2: OA + Sci-Hub（use_scihub={USE_SCIHUB}）")
    results = download_batch(need, OUTPUT_DIR, use_scihub=USE_SCIHUB, delay_sec=1.5)
    pending = [p for p, r in zip(need, results) if not r.ok]

    if not pending:
        all_results = _merge_results(papers, results, OUTPUT_DIR)
        manifest = write_manifest(all_results, OUTPUT_DIR)
        print(format_results_summary(all_results))
        print(f"\nmanifest: {manifest}")
        return 0

    print(f"\n阶段 2/2: 西北大学 CARSI/机构登录补下 {len(pending)} 篇")
    if CREDENTIALS_PATH.is_file():
        print(f"账号配置: {CREDENTIALS_PATH}（已加入 .gitignore）")
    else:
        print("⚠️ 未找到 library_credentials.json，请复制 example 并填写")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        context = None
        try:
            context = p.chromium.launch_persistent_context(
                **build_launch_options(USER_DATA_DIR, proxy)
            )
            page = context.pages[0] if context.pages else context.new_page()
            if not verify_network(page, "启动后"):
                return 1

            if not SKIP_LOGIN:
                if AUTO_LOGIN and CREDENTIALS_PATH.is_file():
                    pub = _publisher_for_doi(pending[0].doi)
                    print(f"[进展] 自动机构登录（{pub} / CARSI）...")
                    ok = ensure_publisher_login(page, pub)
                    if not ok:
                        print_login_guide()
                        input("👉 请在已打开的 Chrome 中完成 IEEE/CARSI 登录，完成后按回车...")
                else:
                    print_login_guide()
                    input("👉 完成出版商 CARSI/机构登录后按回车继续...")

            context.close()
            context = None
            fix_chrome_profile_proxy(USER_DATA_DIR, proxy)
            time.sleep(1)

            context = p.chromium.launch_persistent_context(
                **build_launch_options(USER_DATA_DIR, proxy)
            )
            page = context.pages[0] if context.pages else context.new_page()
            if not verify_network(page, "重置代理后"):
                print("❌ 网络不可用，中止")
                return 1

            result_map = {r.citeKey: r for r in results}
            for paper in pending:
                r = download_paper(paper, OUTPUT_DIR, use_scihub=False, page=page)
                result_map[paper.citeKey] = r
                time.sleep(3)

            results = [result_map[p.citeKey] for p in need]
            page.close()
            context.close()
        except Exception as e:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            print(f"❌ Playwright 失败: {e}")
            return 1

    all_results = _merge_results(papers, results, OUTPUT_DIR)
    manifest = write_manifest(all_results, OUTPUT_DIR)
    print(format_results_summary(all_results))
    print(f"\nmanifest: {manifest}")
    return 0 if all(r.ok for r in all_results) else 1


def _merge_results(all_papers, batch_results, output_dir: Path):
    """Build full result list including already-downloaded items."""
    from download_lib import DownloadResult

    batch_map = {r.citeKey: r for r in batch_results}
    merged = []
    for p in all_papers:
        if p.citeKey in batch_map:
            merged.append(batch_map[p.citeKey])
        elif is_valid_pdf(dest_path_for(output_dir, p)):
            merged.append(
                DownloadResult(p.citeKey, p.doi, True, str(dest_path_for(output_dir, p)), "existing")
            )
        else:
            merged.append(DownloadResult(p.citeKey, p.doi, False, None, None, "missing"))
    return merged


if __name__ == "__main__":
    raise SystemExit(main())
