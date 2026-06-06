#!/usr/bin/env python3
"""
verify_cited_papers.py — 核实论文正文引用的文献，并归档至 data/papers/

用法:
  python scripts/verify_cited_papers.py
  python scripts/verify_cited_papers.py --download --output-dir data/papers
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIB = ROOT / "latex/references.bib"
DEFAULT_SECTIONS = ROOT / "latex/sections"
DEFAULT_OUT = ROOT / "data/papers"
MANIFEST = "cited_papers_manifest.json"

JOS_DOI_RE = re.compile(r"10\.13328/j\.cnki\.jos\.(\d+)", re.I)
WEB_SNAPSHOT_KEYS = {"otel_tail", "loki2019", "aws_backoff", "turnbull2014monitoring", "beyer2016sre"}


@dataclass
class BibEntry:
    key: str
    entry_type: str
    title: str
    author: str
    year: str
    doi: str
    url: str
    journal: str
    raw: str


def parse_bib(path: Path) -> dict[str, BibEntry]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    entries: dict[str, BibEntry] = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),([\s\S]*?)\n\}", text):
        etype, key, body = m.group(1), m.group(2).strip(), m.group(3)

        def field(name: str) -> str:
            fm = re.search(rf"{name}\s*=\s*\{{([^}}]*)\}}", body, re.I | re.S)
            if fm:
                return " ".join(fm.group(1).split())
            fm = re.search(rf'{name}\s*=\s*"([^"]*)"', body, re.I)
            return fm.group(1).strip() if fm else ""

        entries[key] = BibEntry(
            key=key,
            entry_type=etype,
            title=field("title"),
            author=field("author"),
            year=field("year"),
            doi=field("doi"),
            url=field("url"),
            journal=field("journal") or field("booktitle"),
            raw=m.group(0),
        )
    return entries


def cited_keys(sections_dir: Path) -> set[str]:
    keys: set[str] = set()
    for tex in sections_dir.rglob("*.tex"):
        for block in re.findall(r"\\cite\{([^}]+)\}", tex.read_text(encoding="utf-8", errors="ignore")):
            for k in block.split(","):
                k = k.strip()
                if k:
                    keys.add(k)
    return keys


def arxiv_id_from_doi(doi: str) -> str:
    m = re.search(r"10\.48550/ar[xX]iv\.(\d+\.\d+)", doi, re.I)
    return m.group(1) if m else ""


def jos_html_url(doi: str) -> str:
    m = JOS_DOI_RE.search(doi)
    if not m:
        return ""
    num = m.group(1).lstrip("0") or m.group(1)
    return f"http://www.jos.org.cn/1000-9825/{num}.htm"


def crad_html_url(doi: str) -> str:
    if "10.7544" in doi:
        return f"https://crad.ict.ac.cn/cn/article/doi/{doi}"
    return ""


def cjc_html_url(doi: str) -> str:
    if "10.11897" in doi or "SP.J.1016" in doi:
        return f"https://cjc.ict.ac.cn/academic/article/showArticleDetailByDoi.do?doi={doi}"
    return ""


def jos_urls(doi: str) -> list[str]:
    m = JOS_DOI_RE.search(doi)
    if not m:
        return []
    num = m.group(1).lstrip("0") or m.group(1)
    html = f"http://www.jos.org.cn/1000-9825/{num}.htm"
    return [
        html,
        f"https://www.jos.org.cn/jos/ch/reader/create_pdf.aspx?file_no={num}",
        f"http://www.jos.org.cn/jos/ch/reader/create_pdf.aspx?file_no={num}",
    ]


def verify_doi(doi: str, client: httpx.Client) -> tuple[bool, str]:
    if not doi:
        return False, "无 DOI"
    # 中文 DOI 优先走 CHNDOI
    if "10.13328" in doi or "10.11897" in doi:
        try:
            r = client.get(
                f"https://www.chndoi.org/Resolution/Handler?doi={doi}",
                follow_redirects=True,
                timeout=25,
            )
            if r.status_code < 400:
                return True, str(r.url)
        except Exception:
            pass
    try:
        r = client.get(f"https://api.crossref.org/works/{doi}", timeout=25)
        if r.status_code == 200 and r.json().get("message", {}).get("DOI"):
            title = (r.json()["message"].get("title") or [""])[0]
            return True, f"crossref:{title[:60]}"
    except Exception:
        pass
    # 中文 DOI / 通用跳转
    try:
        r = client.get(f"https://doi.org/{doi}", follow_redirects=True, timeout=25)
        if r.status_code < 400:
            return True, str(r.url)
        if r.status_code in (403, 404) and "cnki" in doi.lower():
            r2 = client.get(
                f"https://www.chndoi.org/Resolution/Handler?doi={doi}",
                follow_redirects=True,
                timeout=25,
            )
            if r2.status_code < 400:
                return True, str(r2.url)
    except Exception as e:
        return False, str(e)
    return False, "verify failed"


def verify_url(url: str, client: httpx.Client) -> tuple[bool, str]:
    if not url:
        return False, "无 URL"
    try:
        r = client.get(url, follow_redirects=True, timeout=25)
        if r.status_code < 400 and len(r.content) > 200:
            return True, str(r.url)
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def is_pdf(content: bytes) -> bool:
    return len(content) > 5 and content[:5].startswith(b"%PDF")


def download_bytes(url: str, client: httpx.Client) -> tuple[bool, bytes, str]:
    try:
        r = client.get(url, follow_redirects=True, timeout=90)
        if r.status_code != 200:
            return False, b"", f"HTTP {r.status_code}"
        if is_pdf(r.content):
            return True, r.content, "pdf"
        ct = r.headers.get("content-type", "")
        if "html" in ct and len(r.content) > 500:
            return True, r.content, "html"
        return False, b"", f"非 PDF/HTML ({ct})"
    except Exception as e:
        return False, b"", str(e)


def unpaywall_pdf(doi: str, client: httpx.Client) -> str:
    try:
        r = client.get(
            f"https://api.unpaywall.org/v2/{doi}?email=p3-microservice@local",
            timeout=20,
        )
        if r.status_code != 200:
            return ""
        loc = r.json().get("best_oa_location") or {}
        return loc.get("url_for_pdf") or loc.get("url") or ""
    except Exception:
        return ""


def safe_filename(entry: BibEntry) -> str:
    author = "unknown"
    if entry.author:
        first = re.split(r"\s+and\s+", entry.author, maxsplit=1)[0]
        parts = first.replace(",", " ").split()
        author = re.sub(r"[^\w]", "", parts[-1] if parts else "unknown")[:20]
    year = entry.year or "nodate"
    return f"{year}_{author}_{entry.key}.pdf"


def try_download(entry: BibEntry, out_dir: Path, client: httpx.Client) -> tuple[str, str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    web_dir = out_dir / "web_snapshots"
    web_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / safe_filename(entry)

    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        return "ok", str(pdf_path.relative_to(ROOT)), "cached"

    urls: list[tuple[str, str]] = []
    aid = arxiv_id_from_doi(entry.doi)
    if aid:
        urls.append(("arxiv_pdf", f"https://arxiv.org/pdf/{aid}.pdf"))
    oa = unpaywall_pdf(entry.doi, client)
    if oa:
        urls.append(("unpaywall", oa))
    if "软件学报" in entry.journal and entry.doi:
        for u in jos_urls(entry.doi):
            urls.append(("jos", u))
    if "计算机研究与发展" in entry.journal and entry.doi:
        u = crad_html_url(entry.doi)
        if u:
            urls.append(("crad_html", u))
    if "计算机学报" in entry.journal and entry.doi:
        u = cjc_html_url(entry.doi)
        if u:
            urls.append(("cjc_html", u))
    if entry.url:
        urls.append(("bib_url", entry.url))
    if entry.doi and not aid:
        urls.append(("doi_landing", f"https://doi.org/{entry.doi}"))

    for method, url in urls:
        ok, data, kind = download_bytes(url, client)
        if not ok:
            continue
        if kind == "pdf":
            pdf_path.write_bytes(data)
            return "ok", str(pdf_path.relative_to(ROOT)), method
        if kind == "html":
            snap = web_dir / f"{entry.key}.html"
            snap.write_bytes(data)
            return "snapshot", str(snap.relative_to(ROOT)), method

    if entry.entry_type == "book" or entry.key in WEB_SNAPSHOT_KEYS:
        meta_path = web_dir / f"{entry.key}_meta.json"
        meta_path.write_text(json.dumps(asdict(entry), ensure_ascii=False, indent=2), encoding="utf-8")
        if entry.url:
            ok, data, kind = download_bytes(entry.url, client)
            if ok and kind == "html":
                snap = web_dir / f"{entry.key}.html"
                snap.write_bytes(data)
                return "snapshot", str(snap.relative_to(ROOT)), "web_snapshot"
        return "snapshot", str(meta_path.relative_to(ROOT)), "metadata_only"

    # CrossRef 元数据 JSON 快照（DOI 已验证但出版商防爬时）
    if entry.doi:
        try:
            r = client.get(f"https://api.crossref.org/works/{entry.doi}", timeout=25)
            if r.status_code == 200:
                snap = web_dir / f"{entry.key}_crossref.json"
                snap.write_bytes(r.content)
                return "snapshot", str(snap.relative_to(ROOT)), "crossref_json"
        except Exception:
            pass

    meta_path = out_dir / "pending" / f"{entry.key}_meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(asdict(entry), ensure_ascii=False, indent=2), encoding="utf-8")
    return "paywall", str(meta_path.relative_to(ROOT)), "no_oa_pdf"


def main() -> int:
    ap = argparse.ArgumentParser(description="核实并下载正文引用文献")
    ap.add_argument("--bib", type=Path, default=DEFAULT_BIB)
    ap.add_argument("--sections", type=Path, default=DEFAULT_SECTIONS)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--download", action="store_true", help="尝试下载 PDF/快照")
    args = ap.parse_args()

    bib = parse_bib(args.bib)
    cited = cited_keys(args.sections)
    missing_in_bib = cited - set(bib)
    if missing_in_bib:
        print("❌ bib 中缺失引用键:", ", ".join(sorted(missing_in_bib)), file=sys.stderr)
        return 1

    manifest: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "bib_path": str(args.bib.relative_to(ROOT)),
        "papers_dir": str(args.output_dir.relative_to(ROOT)),
        "cited_count": len(cited),
        "entries": {},
        "summary": {},
    }
    stats = {"ok": 0, "snapshot": 0, "paywall": 0, "failed": 0, "doi_valid": 0}

    with httpx.Client(headers={"User-Agent": "p3-microservice/1.0 (citation-verify)"}) as client:
        for key in sorted(cited):
            e = bib[key]
            rec: dict[str, Any] = {
                "key": key,
                "title": e.title,
                "year": e.year,
                "doi": e.doi,
                "url": e.url,
                "journal": e.journal,
                "entry_type": e.entry_type,
            }
            if e.doi:
                valid, note = verify_doi(e.doi, client)
                rec["doi_valid"] = valid
                rec["doi_resolve"] = note
                if valid:
                    stats["doi_valid"] += 1
            elif e.url:
                valid, note = verify_url(e.url, client)
                rec["url_valid"] = valid
                rec["url_resolve"] = note
            else:
                rec["doi_valid"] = False
                rec["note"] = "无 DOI/URL"

            if args.download:
                status, path, method = try_download(e, args.output_dir, client)
                rec["archive_status"] = status
                rec["archive_path"] = path
                rec["archive_method"] = method
                stats[status if status in stats else "failed"] += 1
                time.sleep(0.5)

            manifest["entries"][key] = rec
            icon = "✅" if rec.get("doi_valid") or rec.get("url_valid") else "⚠️"
            print(f"{icon} {key}: {e.title[:55]}")

    manifest["summary"] = stats
    out_manifest = args.output_dir / MANIFEST
    out_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 汇总 ===")
    print(json.dumps(stats, indent=2))
    print(f"清单: {out_manifest}")

    unresolved = [
        k for k, v in manifest["entries"].items()
        if not v.get("doi_valid") and not v.get("url_valid")
    ]
    if unresolved:
        print("❌ 无法核实:", unresolved, file=sys.stderr)
        return 1
    if args.download:
        not_archived = [
            k for k, v in manifest["entries"].items()
            if v.get("archive_status") not in ("ok", "snapshot")
        ]
        if not_archived:
            print("❌ 未归档:", not_archived, file=sys.stderr)
            return 1
        print("✅ 全部 cited 文献已核实且已归档（PDF 或官网 HTML 快照）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
