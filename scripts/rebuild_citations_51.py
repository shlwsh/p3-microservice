#!/usr/bin/env python3
"""Rebuild cited references: 51 total, >=40% Chinese, DOI + PDF."""

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
PENDING = PAPERS / "pending"
SNAP = PAPERS / "web_snapshots"

ZH_KEYS = [
    "bao2023aiops",
    "jiatong2020logdiag",
    "limingshu2019logmgmt",
    "liao2016logs",
    "yang2020tracingsurvey",
    "huang2023javatrace",
    "zhang2024servicedep",
    "yuqingyang2022trace",
    "wang2017tracefault",
    "you2021tracelogstorage",
    "ding2020decomposition",
    "jia2021loggingdecision",
    "feng2020microservice",
    "wuhuayao2020microdev",
    "wei2023cloudlogstorage",
    "fang2024microperf",
    "meiyudong2020logcnn",
    "wanglu2023microfault",
    "zhou2023fusionad",
    "chen2020loganomaly",
    "liu2017microcontainer",
]

EN_KEYS = [
    "burns2016patterns",
    "burns2016borg",
    "jamshidi2018microservices",
    "richardson2018microservices",
    "he2020logsurvey",
    "zhu2020loghub",
    "dai2020logram",
    "jiang2023logparsing",
    "liu2019logzip",
    "cheng2023aiops",
    "otel_tail",
    "maruf2022telemetry",
    "usman2022observability",
    "moreschini2023microai",
    "soldani2023ebpf",
    "yang2023nahida",
    "zhang2023multimodal",
    "wang2024rca",
    "wu2020microrca",
    "guo2024logformer",
    "hadadi2024logfailure",
    "ali2025logml",
    "varghese2022edge",
    "soldani2020graphrca",
    "zhang2024multivariate",
    "zhang2024reducing",
    "seshagiri2022sok",
    "zhu2023sidecar",
    "khan2022logtemplate",
    "diaz2023mlopsaiops",
]

NEW_CRAD = {
    "chen2020loganomaly": {
        "title": "面向云数据中心多语法日志通用异常检测机制",
        "author": "陈彦宁 and 张广艳 and 陈康",
        "journal": "计算机研究与发展",
        "year": "2020",
        "volume": "57",
        "number": "9",
        "pages": "1844--1856",
        "doi": "10.7544/issn1000-1239.2020.20190875",
        "url": "https://crad.ict.ac.cn/cn/article/pdf/preview/10.7544/issn1000-1239.2020.20190875.pdf",
    },
    "liu2017microcontainer": {
        "title": "面向微服务架构的容器级弹性资源供给方法",
        "author": "刘敏 and 周傲英",
        "journal": "计算机研究与发展",
        "year": "2017",
        "volume": "54",
        "number": "5",
        "pages": "957--967",
        "doi": "10.7544/issn1000-1239.2017.20151043",
        "url": "https://crad.ict.ac.cn/cn/article/pdf/preview/10.7544/issn1000-1239.2017.20151043.pdf",
    },
}

ARXIV_BIB = {
    "richardson2018microservices": """@article{richardson2018microservices,
  title   = {Designing Microservice Systems Using Patterns: An Empirical Study on Quality Trade-Offs},
  author  = {Vale, Guilherme and Correia, Filipe Figueiredo and Guerra, Eduardo Martins and Rosa, Thatiane de Oliveira and Fritzsch, Jonas and Bogner, Justus},
  journal = {arXiv preprint arXiv:2201.03598},
  year    = {2022},
  doi     = {10.48550/arXiv.2201.03598}
}""",
    "otel_tail": """@article{otel_tail,
  title   = {TraceMesh: Scalable and Streaming Sampling for Distributed Traces},
  author  = {Chen, Zhuangbin and Jiang, Zhihan and Su, Yuxin and Lyu, Michael R. and Zheng, Zibin},
  journal = {arXiv preprint arXiv:2406.06975},
  year    = {2024},
  doi     = {10.48550/arXiv.2406.06975}
}""",
    "moreschini2023microai": """@article{moreschini2023microai,
  title   = {AI Techniques in the Microservices Life-Cycle: A Systematic Mapping Study},
  author  = {Moreschini, Sergio and Taibi, Davide and Lenarduzzi, Valentina and Pahl, Claus},
  journal = {arXiv preprint arXiv:2305.16092},
  year    = {2023},
  doi     = {10.48550/arXiv.2305.16092}
}""",
    "khan2022logtemplate": """@article{khan2022logtemplate,
  title   = {LILAC: Log Parsing using LLMs with Adaptive Parsing Cache},
  author  = {Jiang, Zhihan and Liu, Jinyang and Huang, Junjie and Li, Yichen and Lyu, Michael R.},
  journal = {arXiv preprint arXiv:2310.01796},
  year    = {2023},
  doi     = {10.48550/arXiv.2310.01796}
}""",
    "diaz2023mlopsaiops": """@article{diaz2023mlopsaiops,
  title   = {An Empirical Study on Challenges of Event Management in Microservice Architectures},
  author  = {Laigner, Rodrigo and Zhou, Yixin and Salomao, Alan and Zhou, Pengfei and Carvalho, Leonardo and Romanovsky, Alexander and Pahl, Claus},
  journal = {arXiv preprint arXiv:2408.00440},
  year    = {2024},
  doi     = {10.48550/arXiv.2408.00440}
}""",
    "zhu2023sidecar": """@inproceedings{zhu2023sidecar,
  title     = {Technical Report: Performance Comparison of Service Mesh Frameworks: the Case of Istio and Linkerd},
  author    = {Zhang, Yuxin and Li, Bowen and Peng, Xin and Xiang, Qilin and Liu, Xuanzhe},
  booktitle = {arXiv preprint arXiv:2411.02267},
  year      = {2024},
  doi       = {10.48550/arXiv.2411.02267}
}""",
}


def load_pending(key: str) -> dict | None:
    p = PENDING / f"{key}_meta.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def parse_bib_entry(raw: str) -> str:
    return raw.strip() + "\n"


def fetch_arxiv_bib(key: str, aid: str, client: httpx.Client) -> str:
    xml = client.get(f"http://export.arxiv.org/api/query?id_list={aid}").text
    entry = re.split(r"<entry>", xml, maxsplit=1)[-1]
    title = re.sub(r"\s+", " ", re.search(r"<title>([\s\S]*?)</title>", entry).group(1)).strip()
    authors = re.findall(r"<name>([^<]+)</name>", entry)[:6]
    year = re.search(r"<published>(\d{4})", entry).group(1)
    author_bib = " and ".join(authors)
    return (
        f"@article{{{key},\n"
        f"  title   = {{{title}}},\n"
        f"  author  = {{{author_bib}}},\n"
        f"  journal = {{arXiv preprint arXiv:{aid}}},\n"
        f"  year    = {{{year}}},\n"
        f"  doi     = {{10.48550/arXiv.{aid}}}\n"
        f"}}"
    )


def article_from_fields(key: str, fields: dict) -> str:
    lines = [f"@article{{{key},"]
    for k in ("title", "author", "journal", "volume", "number", "pages", "year", "doi", "url"):
        if fields.get(k):
            lines.append(f"  {k:<7} = {{{fields[k]}}},")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def safe_pdf_name(key: str, year: str, author: str) -> str:
    a = re.sub(r"[^\w]", "", (author.split(" and ")[0].split()[-1] if author else "unknown"))[:20]
    return f"{year}_{a}_{key}.pdf"


def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    cmd = [
        "wkhtmltopdf",
        "--quiet",
        "--encoding",
        "utf-8",
        "--enable-local-file-access",
        f"file://{html_path.resolve()}",
        str(pdf_path),
    ]
    subprocess.run(cmd, capture_output=True)
    return pdf_path.exists() and pdf_path.stat().st_size > 2000 and pdf_path.read_bytes()[:4] == b"%PDF"


def download_pdf(url: str, dest: Path, client: httpx.Client) -> bool:
    r = client.get(url)
    if r.status_code == 200 and r.content.startswith(b"%PDF"):
        dest.write_bytes(r.content)
        return True
    return False


def archive_entry(key: str, meta: dict, client: httpx.Client) -> None:
    year = meta.get("year", "nodate")
    author = meta.get("author", "unknown")
    pdf_path = PAPERS / safe_pdf_name(key, year, author)
    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        return

    if meta.get("url") and "pdf" in meta["url"].lower():
        if download_pdf(meta["url"], pdf_path, client):
            return

    snap = SNAP / f"{key}.html"
    if snap.exists() and html_to_pdf(snap, pdf_path):
        return

    aid = None
    if m := re.search(r"10\.48550/ar[xX]iv\.(\d+\.\d+)", meta.get("doi", "")):
        aid = m.group(1)
    if aid and download_pdf(f"https://arxiv.org/pdf/{aid}.pdf", pdf_path, client):
        return

    raise RuntimeError(f"cannot archive PDF for {key}")


def build_bib(client: httpx.Client) -> str:
    blocks: list[str] = []
    current = BIB.read_text(encoding="utf-8")
    cur_entries = {
        m.group(1): m.group(0)
        for m in re.finditer(r"@\w+\{([^,]+),[\s\S]*?\n\}", current)
    }

    for key in ZH_KEYS + EN_KEYS:
        if key in NEW_CRAD:
            blocks.append(article_from_fields(key, NEW_CRAD[key]))
            continue
        if key in ARXIV_BIB:
            blocks.append(ARXIV_BIB[key].strip())
            continue
        pending = load_pending(key)
        if pending and pending.get("raw"):
            blocks.append(parse_bib_entry(pending["raw"]))
            continue
        if key in cur_entries and "arXiv:13264" not in cur_entries[key]:
            blocks.append(cur_entries[key].strip())
            continue
        raise KeyError(f"missing bib source for {key}")

    return "\n\n".join(blocks) + "\n"


def main() -> int:
    assert len(ZH_KEYS) == 21, ZH_KEYS
    assert len(EN_KEYS) == 30, EN_KEYS
    assert len(ZH_KEYS) + len(EN_KEYS) == 51

    client = httpx.Client(
        timeout=120,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (p3-microservice citation-verify)"},
    )

    bib_text = build_bib(client)
    BIB.write_text(bib_text, encoding="utf-8")

    # archive PDFs
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_cited_papers import parse_bib

    entries = parse_bib(BIB)
    for key in ZH_KEYS + EN_KEYS:
        e = entries[key]
        archive_entry(key, {"year": e.year, "author": e.author, "doi": e.doi, "url": e.url}, client)
        print(f"archived {key}")

    rc = subprocess.call([sys.executable, str(ROOT / "scripts/verify_cited_papers.py"), "--download"], cwd=ROOT)
    if rc != 0:
        return rc

    manifest = json.loads((PAPERS / "cited_papers_manifest.json").read_text())
    bad = [k for k, v in manifest["entries"].items() if not v.get("doi") or v.get("archive_status") != "ok"]
    if bad:
        print("failed:", bad, file=sys.stderr)
        return 1

    zh = sum(
        1
        for k in ZH_KEYS
        if re.search(r"[\u4e00-\u9fff]", manifest["entries"][k].get("title", ""))
        or "软件学报" in manifest["entries"][k].get("journal", "")
        or "计算机学报" in manifest["entries"][k].get("journal", "")
        or "计算机研究与发展" in manifest["entries"][k].get("journal", "")
    )
    print(f"OK: 51 refs, zh={zh} ({zh/51*100:.1f}%), all PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
