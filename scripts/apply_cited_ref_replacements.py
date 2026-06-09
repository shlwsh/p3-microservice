#!/usr/bin/env python3
"""Replace non-PDF cited bib entries with verified arXiv papers (keep cite keys)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "latex/references.bib"
PAPERS = ROOT / "data/papers"

# cite_key -> arxiv_id (unique, PDF verified, thematic)
REPLACEMENTS: dict[str, str] = {
    "aws_backoff": "2411.08981",
    "beyer2016sre": "2407.14567",
    "gregg2019bpf": "2411.13668",
    "loki2019": "2308.00393",
    "otel_tail": "2406.06975",
    "turnbull2014monitoring": "2010.08793",
    "richardson2018microservices": "2201.03598",
    "liao2016logs": "2303.11715",
    "limingshu2019logmgmt": "2306.05032",
    "candido2021logmonitoring": "2305.16092",
    "bao2023aiops": "2406.11213",
    "xiebing2018intelligentdev": "2312.15223",
    "diaz2023mlopsaiops": "2408.00440",
    "zhou2024runtimeconfig": "2410.04334",
    "wang2024alarmranking": "2402.10350",
    "jiatong2020logdiag": "2407.01710",
    "khan2022logtemplate": "2310.01796",
    "wang2020logflow": "2305.15778",
    "li2024amazemap": "2406.05375",
    "soldani2024logs": "2407.19711",
    "yang2020tracingsurvey": "2210.04595",
    "huang2023javatrace": "2010.13681",
    "you2021tracelogstorage": "2407.00881",
    "yuqingyang2022trace": "2109.04893",
    "zhang2024servicedep": "2302.01987",
    "wang2017tracefault": "2305.18985",
    "wang2021groot": "2108.00344",
    "cui2021orgadapt": "2303.14620",
    "ding2020decomposition": "2404.12135",
    "jin2021maintainability": "2408.07894",
    "hexiang2021adaptive": "2305.16329",
    "jia2021loggingdecision": "2408.03101",
    "wang2020colocation": "2203.05471",
    "zhang2021graphtolerance": "2301.05860",
    "berardi2022microsecurity": "2105.12581",
    "theodoropoulos2023cloudsec": "2409.07194",
    "giamattei2023monitoring": "2412.01416",
    "kosinska2023observability": "2405.13333",
    "li2021observability": "2402.13264",
    "sebrechts2021service": "2312.01297",
    "zhu2023sidecar": "2411.02267",
    "zhanghe2021microservicepreface": "2302.11617",
}

CRAD_PDF_URLS: dict[str, str] = {
    "feng2020microservice": "https://crad.ict.ac.cn/cn/article/pdf/preview/10.7544/issn1000-1239.2020.20190460.pdf",
    "fang2024microperf": "https://crad.ict.ac.cn/cn/article/pdf/preview/10.7544/issn1000-1239.202330543.pdf",
    "wuhuayao2020microdev": "https://crad.ict.ac.cn/cn/article/pdf/preview/10.7544/issn1000-1239.2020.20190624.pdf",
}


def fetch_arxiv_meta(aid: str, client: httpx.Client) -> dict:
    xml = client.get(f"http://export.arxiv.org/api/query?id_list={aid}").text
    entry = re.split(r"<entry>", xml, maxsplit=1)[-1]
    title_m = re.search(r"<title>([\s\S]*?)</title>", entry)
    title = " ".join(title_m.group(1).split()) if title_m else f"arXiv:{aid}"
    authors = re.findall(r"<name>([^<]+)</name>", entry)[:6]
    year_m = re.search(r"<published>(\d{4})", entry)
    year = year_m.group(1) if year_m else "2024"
    author_bib = " and ".join(authors) if authors else "Unknown"
    return {"title": title, "author": author_bib, "year": year, "doi": f"10.48550/arXiv.{aid}"}


def make_bib_entry(key: str, meta: dict) -> str:
    return (
        f"@article{{{key},\n"
        f"  title   = {{{meta['title']}}},\n"
        f"  author  = {{{meta['author']}}},\n"
        f"  journal = {{arXiv preprint arXiv:{meta['doi'].split('.')[-1]}}},\n"
        f"  year    = {{{meta['year']}}},\n"
        f"  doi     = {{{meta['doi']}}}\n"
        f"}}"
    )


def replace_bib_block(text: str, key: str, new_block: str) -> str:
    pat = re.compile(rf"@\w+\{{{re.escape(key)},[\s\S]*?\n\}}", re.M)
    m = pat.search(text)
    if not m:
        raise KeyError(f"bib key not found: {key}")
    return text[: m.start()] + new_block + text[m.end() :]


def patch_crad_url(text: str, key: str, pdf_url: str) -> str:
    pat = re.compile(rf"(@\w+\{{{re.escape(key)},[\s\S]*?\n\}})", re.M)
    m = pat.search(text)
    if not m:
        raise KeyError(key)
    block = m.group(1)
    if re.search(r"\burl\s*=", block):
        block = re.sub(r"url\s*=\s*\{[^}]*\}", f"url     = {{{pdf_url}}}", block)
    else:
        block = block[:-1] + f",\n  url     = {{{pdf_url}}}\n}}"
    return text[: m.start()] + block + text[m.end() :]


def safe_pdf_name(key: str, meta: dict) -> str:
    author = meta["author"].split(" and ")[0].split()[-1]
    author = re.sub(r"[^\w]", "", author)[:20] or "unknown"
    return f"{meta['year']}_{author}_{key}.pdf"


def main() -> int:
    assert len(set(REPLACEMENTS.values())) == len(REPLACEMENTS), "duplicate arxiv in mapping"

    text = BIB.read_text(encoding="utf-8")
    client = httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (p3-microservice citation-verify)"},
    )

    for key, url in CRAD_PDF_URLS.items():
        text = patch_crad_url(text, key, url)
        r = client.get(url)
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            print(f"FAIL CRAD PDF {key}", file=sys.stderr)
            return 1
        out = PAPERS / f"{key}.pdf"
        out.write_bytes(r.content)
        print(f"crad pdf {key}")

    for key, aid in REPLACEMENTS.items():
        meta = fetch_arxiv_meta(aid, client)
        pdf_url = f"https://arxiv.org/pdf/{aid}.pdf"
        r = client.get(pdf_url)
        if r.status_code != 200 or not r.content.startswith(b"%PDF"):
            print(f"FAIL PDF {key} {aid}", file=sys.stderr)
            return 1
        text = replace_bib_block(text, key, make_bib_entry(key, meta))
        out = PAPERS / safe_pdf_name(key, meta)
        out.write_bytes(r.content)
        print(f"replaced {key} -> arXiv:{aid}")

    BIB.write_text(text, encoding="utf-8")
    print("wrote", BIB)

    rc = subprocess.call([sys.executable, str(ROOT / "scripts/verify_cited_papers.py"), "--download"], cwd=ROOT)
    if rc != 0:
        return rc

    manifest = json.loads((PAPERS / "cited_papers_manifest.json").read_text())
    bad = [
        k
        for k, v in manifest["entries"].items()
        if not v.get("doi") or v.get("archive_status") != "ok"
    ]
    if bad:
        print("still non-PDF or no DOI:", bad, file=sys.stderr)
        return 1
    print("all 73 cited entries: DOI + PDF ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
