import json
import os
import sys
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from download_lib import (  # noqa: E402
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT,
    PaperItem,
    download_batch,
    download_paper,
    format_results_summary,
    load_paper_config,
    write_manifest,
)

mcp = FastMCP("ScholarDownloader")


def _abs_output(output_dir: str) -> Path:
    p = Path(output_dir)
    if not p.is_absolute():
        # workspace root = scholar-downloader/../../..
        workspace = ROOT.parents[2]
        p = workspace / output_dir
    p.mkdir(parents=True, exist_ok=True)
    return p


@mcp.tool()
def download_papers(
    dois: list[str],
    output_dir: str = "data/papers",
    use_scihub: bool = True,
) -> str:
    """
    Download academic papers by DOI. Tries open access first, then Sci-Hub (scidownl/HTTP).

    Args:
        dois: DOI list, e.g. ["10.1109/TIP.2024.3378466"]
        output_dir: Save directory (relative to workspace root)
        use_scihub: Whether to use Sci-Hub when OA fails (default True)
    """
    out = _abs_output(output_dir)
    papers = [
        PaperItem(citeKey=doi.replace("/", "_").replace(".", "_"), doi=doi, title=doi)
        for doi in dois
    ]
    results = download_batch(papers, out, use_scihub=use_scihub, delay_sec=2.0)
    manifest = write_manifest(results, out)
    return format_results_summary(results) + f"\n\nmanifest: {manifest}"


@mcp.tool()
def download_project_missing(
    output_dir: str = "data/papers",
    use_scihub: bool = True,
    playwright_fallback: bool = False,
) -> str:
    """
    Batch download missing project references (citeKey-named PDFs).

    Strategy: known open URL → Unpaywall → publisher direct → Sci-Hub.
    Set playwright_fallback=True to open Chrome for institutional SSO on failures
    (run from terminal; requires user login when prompted).

    Args:
        output_dir: Save directory
        use_scihub: Use Sci-Hub when OA fails
        playwright_fallback: Launch Playwright for remaining items
    """
    out = _abs_output(output_dir)
    
    scripts_dir = str(ROOT.parents[2] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from verify_cited_papers import parse_bib, cited_keys, DEFAULT_BIB, DEFAULT_SECTIONS
        bib = parse_bib(DEFAULT_BIB)
        cited = cited_keys(DEFAULT_SECTIONS)
        papers = []
        for key in cited:
            if key in bib:
                e = bib[key]
                if e.doi or e.url:
                    papers.append(PaperItem(
                        citeKey=e.key,
                        doi=e.doi or "",
                        title=e.title,
                        author=e.author,
                        year=e.year,
                        openUrl=e.url
                    ))
    except Exception as e:
        return f"❌ Failed to parse project references: {e}"
    results = download_batch(papers, out, use_scihub=use_scihub, delay_sec=2.0)

    pending = [p for p, r in zip(papers, results) if not r.ok]
    if pending and playwright_fallback:
        try:
            from browser_session import (
                build_launch_options,
                fix_chrome_profile_proxy,
                proxy_server_url,
                verify_network,
            )
            from library_auth import CREDENTIALS_PATH, ensure_publisher_login
            from playwright.sync_api import sync_playwright

            user_data_dir = str(ROOT / "chrome_profile")
            proxy = proxy_server_url()
            result_map = {r.citeKey: r for r in results}

            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    **build_launch_options(user_data_dir, proxy)
                )
                page = context.pages[0] if context.pages else context.new_page()
                verify_network(page, "启动后")
                if CREDENTIALS_PATH.is_file():
                    ensure_publisher_login(page, "ieee")
                context.close()
                fix_chrome_profile_proxy(user_data_dir, proxy)
                time.sleep(1)
                context = p.chromium.launch_persistent_context(
                    **build_launch_options(user_data_dir, proxy)
                )
                page = context.pages[0] if context.pages else context.new_page()
                for paper in pending:
                    r = download_paper(paper, out, use_scihub=False, page=page)
                    result_map[paper.citeKey] = r
                page.close()
                context.close()
            results = [result_map[p.citeKey] for p in papers]
        except Exception as e:
            return (
                format_results_summary(results)
                + f"\n\n⚠️ Playwright fallback failed: {e}\n"
                + "Run: python run_playwright_download.py"
            )

    manifest = write_manifest(results, out)
    tip = (
        "\n\nTip: python scripts/verify_cited_papers.py"
        if all(r.ok for r in results)
        else "\n\nTip: run .venv/bin/python run_playwright_download.py for SSO fallback"
    )
    return format_results_summary(results) + f"\n\nmanifest: {manifest}" + tip


# --- Legacy Selenium + LLM browser tool (CDP attach) ---

import re
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

_workspace = ROOT.parents[2]
for env_path in (_workspace / ".env.mygit", _workspace / ".env"):
    if env_path.is_file():
        load_dotenv(env_path)
        break


def ask_llm_for_xpath(elements_list):
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model = os.environ.get("DASHSCOPE_MODEL", "deepseek-v3")
    if not api_key:
        return None
    prompt = f"""You are an expert at web scraping. I have a list of clickable elements from a web page (academic publisher).
My goal is to download the PDF of the paper.
Please identify the BEST element that represents the "Download PDF" or "View PDF" button.
Return ONLY the EXACT 'xpath' value of that element as a plain string. No markdown, no quotes, no explanation.

Elements:
{json.dumps(elements_list, indent=2)}
"""
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=30,
        )
        resp_data = resp.json()
        if "choices" in resp_data and len(resp_data["choices"]) > 0:
            return resp_data["choices"][0]["message"]["content"].strip("`'\"\n ")
    except Exception as e:
        print(f"LLM Error: {e}")
    return None


def download_pdf_with_cookies(driver, url, dest_path):
    if not url:
        return False
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    try:
        user_agent = driver.execute_script("return navigator.userAgent;")
        session.headers.update({"User-Agent": user_agent})
        res = session.get(url, stream=True, timeout=30)
        content_type = res.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type or res.url.lower().endswith(".pdf"):
            with open(dest_path, "wb") as f:
                for chunk in res.iter_content(1024):
                    f.write(chunk)
            return True
        if "text/html" in content_type:
            match = re.search(r'<iframe[^>]*src="([^"]+)"', res.text, re.IGNORECASE)
            if match:
                pdf_url = match.group(1)
                if pdf_url.startswith("//"):
                    pdf_url = "https:" + pdf_url
                elif pdf_url.startswith("/"):
                    from urllib.parse import urlparse

                    parsed = urlparse(url)
                    pdf_url = f"{parsed.scheme}://{parsed.netloc}{pdf_url}"
                res2 = session.get(pdf_url, stream=True, timeout=30)
                if res2.status_code == 200:
                    with open(dest_path, "wb") as f:
                        for chunk in res2.iter_content(1024):
                            f.write(chunk)
                    with open(dest_path, "rb") as f:
                        if f.read(4) == b"%PDF":
                            return True
                    os.remove(dest_path)
    except Exception as e:
        print(f"Download failed via requests: {e}")
    return False


@mcp.tool()
def download_papers_via_browser(
    dois: list[str],
    output_dir: str = "data/papers",
    debug_port: int = 9222,
    debug_host: str = "127.0.0.1",
) -> str:
    """
    Download papers via Chrome remote debugging (Selenium + optional LLM XPath).
    Launch Chrome with: --remote-debugging-port=9222
    """
    abs_output_dir = str(_abs_output(output_dir))
    results = []
    options = Options()
    options.add_experimental_option("debuggerAddress", f"{debug_host}:{debug_port}")
    try:
        service = ChromeService(ChromeDriverManager(driver_version="148.0.7778.218").install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        return f"❌ Failed to connect to Chrome: {e}"

    original_window = driver.current_window_handle
    driver.switch_to.new_window("tab")
    js_extractor = """
    function getElementXPath(elt) {
        var path = "";
        for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
            var idx = 1;
            for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                if (sib.nodeType == 1 && sib.tagName == elt.tagName) idx++;
            }
            var xname = elt.tagName.toLowerCase();
            if (idx > 1) xname += "[" + idx + "]";
            path = "/" + xname + path;
        }
        return path;
    }
    var candidates = [];
    var elements = document.querySelectorAll('a, button');
    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var text = (el.innerText || el.textContent || el.title || el.getAttribute("aria-label") || "").trim().toLowerCase();
        if (text.length > 0 && (text.includes("pdf") || text.includes("download") || text.includes("article") || text.includes("full text") || el.className.toLowerCase().includes("pdf"))) {
            candidates.push({
                "tag": el.tagName, "text": text, "class": el.className,
                "href": el.href || "", "xpath": getElementXPath(el)
            });
        }
    }
    return candidates.slice(0, 50);
    """

    for doi in dois:
        success = False
        safe_name = doi.replace("/", "_").replace(".", "_")
        dest_path = os.path.join(abs_output_dir, f"llm_downloaded_{safe_name}.pdf")
        for url in [f"https://doi.org/{doi}"]:
            try:
                driver.get(url)
                time.sleep(6)
                pdf_direct_url = None
                try:
                    meta_tag = driver.find_element(By.XPATH, "//meta[@name='citation_pdf_url']")
                    pdf_direct_url = meta_tag.get_attribute("content")
                except Exception:
                    pass
                if pdf_direct_url and download_pdf_with_cookies(driver, pdf_direct_url, dest_path):
                    success = True
                    break
                candidates = driver.execute_script(js_extractor)
                found_xpath = ask_llm_for_xpath(candidates) if candidates else None
                if found_xpath:
                    btn = driver.find_element(By.XPATH, found_xpath)
                    btn_href = btn.get_attribute("href")
                    if download_pdf_with_cookies(driver, btn_href, dest_path):
                        success = True
                        break
            except Exception as e:
                print(f"Failed {url}: {e}")
        results.append(f"{'✅' if success else '⚠️'} {doi}")

    try:
        driver.close()
        driver.switch_to.window(original_window)
    except Exception:
        pass
    return "\n".join(results)


if __name__ == "__main__":
    mcp.run()
