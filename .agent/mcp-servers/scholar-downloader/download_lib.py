"""Shared paper download strategies: OA → Sci-Hub → Playwright."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT.parents[2] / "data" / "papers"
DEFAULT_CONFIG = ROOT.parents[2] / "data" / "papers" / "cited_papers_manifest.json"
DEFAULT_PROXY = "http://127.0.0.1:7890"
SCIHUB_MIRRORS = (
    "https://sci-hub.mk",
    "https://sci-hub.ru",
    "https://sci-hub.se",
    "https://sci-hub.st",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


@dataclass
class PaperItem:
    citeKey: str
    doi: str
    title: str
    author: str = ""
    year: str = ""
    openUrl: str | None = None
    replaces: str | None = None


@dataclass
class DownloadResult:
    citeKey: str
    doi: str
    ok: bool
    path: str | None = None
    source: str | None = None
    error: str | None = None


def load_paper_config(config_path: Path | None = None) -> list[PaperItem]:
    path = config_path or DEFAULT_CONFIG
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [PaperItem(**item) for item in raw]


def _normalize_proxy_url(server: str) -> str:
    server = server.strip()
    if not server:
        return ""
    if "://" not in server:
        return f"http://{server}"
    return server


def get_system_proxy() -> str | None:
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            ) as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if enabled:
                    server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    if server:
                        return _normalize_proxy_url(server.split(";")[0])
        except OSError:
            pass
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        value = os.environ.get(var)
        if value:
            return _normalize_proxy_url(value)
    return None


def resolve_proxy() -> dict[str, str] | None:
    proxy_url = os.environ.get("SCHOLAR_PROXY") or get_system_proxy() or DEFAULT_PROXY
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def is_valid_pdf(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    with open(path, "rb") as f:
        return f.read(4) == b"%PDF"


def dest_path_for(output_dir: Path, paper: PaperItem) -> Path:
    author = "unknown"
    if paper.author:
        first = re.split(r"\s+and\s+", paper.author, maxsplit=1)[0]
        parts = first.replace(",", " ").split()
        author = re.sub(r"[^\w]", "", parts[-1] if parts else "unknown")[:20]
    year = paper.year or "nodate"
    filename = f"{year}_{author}_{paper.citeKey}.pdf"
    return output_dir / filename


def save_pdf_bytes(data: bytes, dest: Path) -> bool:
    if len(data) < 1024 or data[:4] != b"%PDF":
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return is_valid_pdf(dest)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"})
    proxies = resolve_proxy()
    if proxies:
        s.proxies.update(proxies)
    return s


def download_url_to_file(url: str, dest: Path, timeout: int = 60, session: requests.Session | None = None) -> bool:
    try:
        sess = session or _session()
        resp = sess.get(url, timeout=timeout, allow_redirects=True, stream=True)
        if resp.status_code != 200:
            return False
        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            # HTML wrapper may embed iframe PDF
            text = resp.text[:50000]
            m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', text, re.I)
            if m:
                pdf_url = urljoin(resp.url, m.group(1))
                resp = sess.get(pdf_url, timeout=timeout, stream=True)
            else:
                m = re.search(r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']', text, re.I)
                if m:
                    pdf_url = urljoin(resp.url, m.group(1))
                    resp = sess.get(pdf_url, timeout=timeout, stream=True)
                else:
                    return False
        data = resp.content
        return save_pdf_bytes(data, dest)
    except Exception:
        return False


def try_open_access(paper: PaperItem, dest: Path) -> DownloadResult | None:
    if paper.openUrl and download_url_to_file(paper.openUrl, dest):
        return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "openUrl")

    # Unpaywall
    email = os.environ.get("UNPAYWALL_EMAIL", "dev@p3-microservice.local")
    try:
        resp = _session().get(
            f"https://api.unpaywall.org/v2/{paper.doi}?email={email}",
            timeout=20,
        )
        if resp.status_code == 200:
            best = resp.json().get("best_oa_location") or {}
            oa_url = best.get("url_for_pdf") or best.get("url")
            if oa_url and download_url_to_file(oa_url, dest):
                return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "unpaywall")
    except Exception:
        pass

    # Publisher-specific direct candidates
    candidates: list[str] = []
    if paper.doi.startswith("10.1109/"):
        arnum = paper.doi.split("/")[-1].split(".")[-1]
        if arnum.isdigit():
            candidates.append(
                f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber={arnum}"
            )
    if paper.doi.startswith("10.1007/"):
        candidates.append(f"https://link.springer.com/content/pdf/{paper.doi}.pdf")
    if paper.doi.startswith("10.1016/"):
        pii = paper.doi.split("/", 1)[-1]
        candidates.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft")

    for url in candidates:
        if download_url_to_file(url, dest):
            return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "publisher_direct")
    return None


def _scidownl_env() -> dict[str, str]:
    env = os.environ.copy()
    proxy_url = (resolve_proxy() or {}).get("http")
    if proxy_url:
        env["HTTP_PROXY"] = proxy_url
        env["HTTPS_PROXY"] = proxy_url
    return env


def try_scihub_scidownl(paper: PaperItem, dest: Path, output_dir: Path) -> DownloadResult | None:
    scidownl = Path(sys.executable).parent / "scidownl"
    exe = scidownl if scidownl.is_file() else scidownl.with_suffix(".exe")
    if exe.is_file():
        before = {p.name for p in output_dir.glob("*.pdf")}
        try:
            subprocess.run(
                [str(exe), "download", "--doi", paper.doi, "--out", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=120,
                env=_scidownl_env(),
            )
            if dest.is_file() and is_valid_pdf(dest):
                return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "scidownl")
            after = [p for p in output_dir.glob("*.pdf") if p.name not in before]
            for pdf in after:
                if is_valid_pdf(pdf):
                    if pdf != dest:
                        pdf.replace(dest)
                    return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "scidownl")
        except Exception:
            pass
    return try_scihub_http(paper, dest)


def try_scihub_http(paper: PaperItem, dest: Path) -> DownloadResult | None:
    session = _session()
    for mirror in SCIHUB_MIRRORS:
        try:
            resp = session.get(f"{mirror}/{paper.doi}", timeout=30, allow_redirects=True)
            if resp.status_code != 200:
                continue
            html = resp.text
            pdf_url = None
            for pattern in (
                r'<embed[^>]+src=["\']([^"\']+)["\']',
                r'<iframe[^>]+src=["\']([^"\']+)["\']',
                r'id=["\']pdf["\'][^>]*src=["\']([^"\']+)["\']',
                r'location\.href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']',
                r'//sci[^"\']+\.pdf',
            ):
                m = re.search(pattern, html, re.I)
                if m:
                    pdf_url = m.group(1) if m.lastindex else m.group(0)
                    pdf_url = urljoin(resp.url, pdf_url)
                    break
            if not pdf_url:
                continue
            if pdf_url.startswith("//"):
                pdf_url = "https:" + pdf_url
            if download_url_to_file(pdf_url, dest):
                return DownloadResult(paper.citeKey, paper.doi, True, str(dest), f"scihub:{mirror}")
        except Exception:
            continue
    return None


def _ieee_urls(doi: str) -> list[str]:
    arnum = doi.split("/")[-1].split(".")[-1]
    urls = [f"https://doi.org/{doi}"]
    if arnum.isdigit():
        urls.append(f"https://ieeexplore.ieee.org/document/{arnum}")
        urls.append(
            f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?arnumber={arnum}&ref="
        )
    return urls


def try_playwright_single(paper: PaperItem, dest: Path, page) -> DownloadResult | None:
    """Download one paper using an existing Playwright page (logged-in browser)."""
    try:
        urls = _ieee_urls(paper.doi) if paper.doi.startswith("10.1109/") else [f"https://doi.org/{paper.doi}"]
        for url in urls:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(4000)
            if "stampPDF" in url or "getPDF.jsp" in url:
                sess = _session()
                for c in page.context.cookies():
                    sess.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
                if download_url_to_file(page.url, dest, session=sess):
                    return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "playwright_stamp")

            meta = page.locator("meta[name='citation_pdf_url']")
            if meta.count() > 0:
                pdf_url = meta.first.get_attribute("content")
                if pdf_url:
                    page.goto(pdf_url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3000)

            selectors = (
                "a[href$='.pdf'], a:has-text('PDF'), button:has-text('PDF'), "
                "a[title*='PDF'], button[title*='PDF'], .pdf-download, "
                "a[aria-label*='Download PDF'], a[aria-label*='PDF'], "
                "a[href*='stampPDF'], a[href*='getPDF']"
            )
            link = page.locator(selectors).first
            if link.count() > 0:
                try:
                    with page.expect_download(timeout=30000) as dl_info:
                        link.click()
                    dl = dl_info.value
                    dl.save_as(str(dest))
                    if is_valid_pdf(dest):
                        return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "playwright_click")
                except Exception:
                    href = link.get_attribute("href")
                    if href and download_url_to_file(href, dest):
                        return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "playwright_href")

            if page.url.lower().endswith(".pdf") or "stamppdf" in page.url.lower():
                cookies = page.context.cookies()
                sess = _session()
                for c in cookies:
                    sess.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))
                if download_url_to_file(page.url, dest):
                    return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "playwright_pdf_url")
    except Exception:
        pass
    return None


def download_paper(
    paper: PaperItem,
    output_dir: Path,
    *,
    use_scihub: bool = True,
    page=None,
) -> DownloadResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_path_for(output_dir, paper)
    if is_valid_pdf(dest):
        return DownloadResult(paper.citeKey, paper.doi, True, str(dest), "existing")

    for fn in (try_open_access,):
        result = fn(paper, dest)
        if result:
            return result

    if use_scihub:
        result = try_scihub_scidownl(paper, dest, output_dir)
        if result:
            return result

    if page is not None:
        result = try_playwright_single(paper, dest, page)
        if result:
            return result

    return DownloadResult(
        paper.citeKey,
        paper.doi,
        False,
        None,
        None,
        "all strategies failed",
    )


def download_batch(
    papers: list[PaperItem],
    output_dir: Path,
    *,
    use_scihub: bool = True,
    page=None,
    delay_sec: float = 3.0,
) -> list[DownloadResult]:
    results: list[DownloadResult] = []
    for i, paper in enumerate(papers):
        print(f"[{i + 1}/{len(papers)}] {paper.citeKey} ({paper.doi})")
        result = download_paper(paper, output_dir, use_scihub=use_scihub, page=page)
        results.append(result)
        status = "✅" if result.ok else "❌"
        print(f"  {status} {result.source or result.error}")
        if i + 1 < len(papers) and delay_sec > 0:
            time.sleep(delay_sec)
    return results


def write_manifest(results: list[DownloadResult], output_dir: Path) -> Path:
    manifest_path = output_dir / "download_manifest.json"
    payload = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outputDir": str(output_dir.resolve()),
        "summary": {
            "total": len(results),
            "success": sum(1 for r in results if r.ok),
            "failed": sum(1 for r in results if not r.ok),
        },
        "items": [
            {
                "citeKey": r.citeKey,
                "doi": r.doi,
                "ok": r.ok,
                "path": r.path,
                "source": r.source,
                "error": r.error,
            }
            for r in results
        ],
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return manifest_path


def format_results_summary(results: list[DownloadResult]) -> str:
    lines = []
    for r in results:
        if r.ok:
            lines.append(f"✅ {r.citeKey} ({r.doi}) ← {r.source}\n   {r.path}")
        else:
            lines.append(f"❌ {r.citeKey} ({r.doi}) — {r.error}")
    ok = sum(1 for r in results if r.ok)
    lines.append(f"\n合计: {ok}/{len(results)} 成功")
    return "\n".join(lines)
