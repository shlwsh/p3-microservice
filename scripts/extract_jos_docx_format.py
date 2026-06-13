#!/usr/bin/env python3
"""Extract formatting definitions from the JOS 2025 Word sample docx."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs/latex-models/software-journal/软件学报排版样例2025年版.docx"
OUT_DIR = ROOT / "docs/format"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def w(name: str) -> str:
    return f"{{{NS['w']}}}{name}"


def qattr(el: ET.Element | None, name: str) -> str | None:
    return el.get(w(name)) if el is not None else None


def twip_to_cm(value: str | None) -> float | None:
    return round(int(value) / 567, 3) if value is not None else None


def twip_to_pt(value: str | None) -> float | None:
    return round(int(value) / 20, 2) if value is not None else None


def halfpt(value: str | None) -> float | None:
    return round(int(value) / 2, 2) if value is not None else None


def attrs(el: ET.Element | None) -> dict[str, str]:
    if el is None:
        return {}
    return {k.split("}", 1)[-1]: v for k, v in el.attrib.items()}


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.findall(".//w:t", NS))


def paragraph_style(p: ET.Element) -> str:
    ppr = p.find("w:pPr", NS)
    pstyle = ppr.find("w:pStyle", NS) if ppr is not None else None
    return qattr(pstyle, "val") or "(none)"


def paragraph_format(p: ET.Element) -> dict[str, Any]:
    ppr = p.find("w:pPr", NS)
    spacing = ppr.find("w:spacing", NS) if ppr is not None else None
    ind = ppr.find("w:ind", NS) if ppr is not None else None
    jc = ppr.find("w:jc", NS) if ppr is not None else None
    pstyle = paragraph_style(p)
    first_rpr = None
    for r in p.findall("w:r", NS):
        first_rpr = r.find("w:rPr", NS)
        if first_rpr is not None:
            break
    sz = first_rpr.find("w:sz", NS) if first_rpr is not None else None
    rfonts = first_rpr.find("w:rFonts", NS) if first_rpr is not None else None
    bold = first_rpr.find("w:b", NS) is not None if first_rpr is not None else False
    italic = first_rpr.find("w:i", NS) is not None if first_rpr is not None else False
    return {
        "style_id": pstyle,
        "alignment": qattr(jc, "val"),
        "spacing_twips": attrs(spacing),
        "spacing_pt": {k: twip_to_pt(v) for k, v in attrs(spacing).items() if v.isdigit()},
        "indent_twips": attrs(ind),
        "indent_cm": {k: twip_to_cm(v) for k, v in attrs(ind).items() if v.lstrip("-").isdigit()},
        "first_run_size_pt": halfpt(qattr(sz, "val")),
        "first_run_fonts": attrs(rfonts),
        "first_run_bold": bold,
        "first_run_italic": italic,
    }


def style_record(st: ET.Element) -> dict[str, Any]:
    ppr = st.find("w:pPr", NS)
    rpr = st.find("w:rPr", NS)
    spacing = ppr.find("w:spacing", NS) if ppr is not None else None
    ind = ppr.find("w:ind", NS) if ppr is not None else None
    jc = ppr.find("w:jc", NS) if ppr is not None else None
    sz = rpr.find("w:sz", NS) if rpr is not None else None
    rfonts = rpr.find("w:rFonts", NS) if rpr is not None else None
    return {
        "style_id": st.get(w("styleId")),
        "type": st.get(w("type")),
        "name": qattr(st.find("w:name", NS), "val"),
        "based_on": qattr(st.find("w:basedOn", NS), "val"),
        "next": qattr(st.find("w:next", NS), "val"),
        "alignment": qattr(jc, "val"),
        "spacing_twips": attrs(spacing),
        "spacing_pt": {k: twip_to_pt(v) for k, v in attrs(spacing).items() if v.isdigit()},
        "indent_twips": attrs(ind),
        "indent_cm": {k: twip_to_cm(v) for k, v in attrs(ind).items() if v.lstrip("-").isdigit()},
        "font_size_pt": halfpt(qattr(sz, "val")),
        "fonts": attrs(rfonts),
        "bold": rpr.find("w:b", NS) is not None if rpr is not None else False,
        "italic": rpr.find("w:i", NS) is not None if rpr is not None else False,
    }


def classify_paragraph(txt: str) -> str:
    if not txt.strip():
        return "empty"
    if txt.startswith("图"):
        return "figure_caption"
    if txt.startswith("表"):
        return "table_caption"
    if txt in {"References", "附中文参考文献"}:
        return "reference_heading"
    if re.match(r"^\[\d+\]", txt):
        return "reference_item"
    if txt.startswith(("中文引用格式", "英文引用格式")):
        return "citation_format"
    if txt.startswith(("摘  要", "Abstract:")):
        return "abstract"
    if txt.startswith(("关键词", "Key words")):
        return "keywords"
    return "body_or_heading"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(DOCX) as zf:
        document = ET.fromstring(zf.read("word/document.xml"))
        styles = ET.fromstring(zf.read("word/styles.xml"))
        rels = ET.fromstring(zf.read("word/_rels/document.xml.rels"))
        headers = {
            name: ET.fromstring(zf.read(name))
            for name in zf.namelist()
            if name.startswith("word/header") and name.endswith(".xml")
        }
        footers = {
            name: ET.fromstring(zf.read(name))
            for name in zf.namelist()
            if name.startswith("word/footer") and name.endswith(".xml")
        }
        media = [name for name in zf.namelist() if name.startswith("word/media/")]
        embeddings = [name for name in zf.namelist() if name.startswith("word/embeddings/")]

    sect = document.find(".//w:sectPr", NS)
    pg_sz = sect.find("w:pgSz", NS) if sect is not None else None
    pg_mar = sect.find("w:pgMar", NS) if sect is not None else None
    cols = sect.find("w:cols", NS) if sect is not None else None
    page_setup = {
        "paper_twips": attrs(pg_sz),
        "paper_cm": {
            "width": twip_to_cm(qattr(pg_sz, "w")),
            "height": twip_to_cm(qattr(pg_sz, "h")),
        },
        "margins_twips": attrs(pg_mar),
        "margins_cm": {k: twip_to_cm(v) for k, v in attrs(pg_mar).items()},
        "columns": attrs(cols),
        "title_page_enabled": sect.find("w:titlePg", NS) is not None if sect is not None else False,
        "header_references": [attrs(x) for x in sect.findall("w:headerReference", NS)] if sect is not None else [],
        "footer_references": [attrs(x) for x in sect.findall("w:footerReference", NS)] if sect is not None else [],
    }

    style_records = [style_record(st) for st in styles.findall("w:style", NS)]
    paragraphs = document.findall(".//w:body/w:p", NS)
    paragraph_records = []
    for i, p in enumerate(paragraphs, 1):
        txt = text_of(p).strip()
        if not txt:
            continue
        rec = paragraph_format(p)
        rec.update({"index": i, "text": txt, "class": classify_paragraph(txt)})
        paragraph_records.append(rec)

    header_footer = {
        "headers": {
            name: [text_of(p).strip() for p in root.findall(".//w:p", NS) if text_of(p).strip()]
            for name, root in headers.items()
        },
        "footers": {
            name: [text_of(p).strip() for p in root.findall(".//w:p", NS) if text_of(p).strip()]
            for name, root in footers.items()
        },
    }

    relationships = [
        {k.split("}", 1)[-1]: v for k, v in rel.attrib.items()}
        for rel in rels
    ]
    summary = {
        "source_docx": str(DOCX.relative_to(ROOT)),
        "page_setup": page_setup,
        "style_count": len(style_records),
        "paragraph_count": len(paragraphs),
        "nonempty_paragraph_count": len(paragraph_records),
        "paragraph_style_counts": Counter(r["style_id"] for r in paragraph_records).most_common(),
        "paragraph_class_counts": Counter(r["class"] for r in paragraph_records).most_common(),
        "media_count": len(media),
        "embedding_count": len(embeddings),
    }
    data = {
        "summary": summary,
        "page_setup": page_setup,
        "styles": style_records,
        "paragraphs": paragraph_records,
        "caption_paragraphs": [r for r in paragraph_records if r["class"] in {"figure_caption", "table_caption"}],
        "reference_paragraphs": [r for r in paragraph_records if r["class"].startswith("reference")],
        "header_footer": header_footer,
        "relationships": relationships,
        "media": media,
        "embeddings": embeddings,
    }
    json_path = OUT_DIR / "jos_2025_docx_format_definitions.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 软件学报 2025 年版 Word 样例格式定义提取",
        "",
        f"源文件：`{DOCX.relative_to(ROOT)}`",
        "",
        "## 1. 页面设置",
        "",
        "| 项 | Word XML 值 | 换算 |",
        "|----|------------|------|",
        f"| 纸张 | `{page_setup['paper_twips']}` | {page_setup['paper_cm']['width']} cm × {page_setup['paper_cm']['height']} cm |",
        f"| 页边距 | `{page_setup['margins_twips']}` | {page_setup['margins_cm']} |",
        f"| 分栏 | `{page_setup['columns']}` | 单栏 |",
        f"| 首页独立页眉页脚 | `{page_setup['title_page_enabled']}` | Word `titlePg` |",
        "",
        "## 2. 页眉页脚文本",
        "",
    ]
    for kind, mapping in header_footer.items():
        md_lines.append(f"### {kind}")
        for name, texts in mapping.items():
            md_lines.append(f"- `{name}`: {' | '.join(texts) if texts else '(empty)'}")
        md_lines.append("")
    md_lines.extend([
        "## 3. 关键样式定义",
        "",
        "| styleId | 名称 | 类型 | 对齐 | 字号 pt | 字体 | 段前/段后/行距 | 缩进 |",
        "|---------|------|------|------|---------|------|----------------|------|",
    ])
    wanted = {
        "1", "64", "65", "66", "112", "113", "115", "117", "118", "120", "121",
        "126", "129", "130", "132", "145", "149", "207", "213", "215", "225",
    }
    for r in style_records:
        if r["style_id"] in wanted or (r["name"] and any(x in r["name"] for x in ["参考", "标题", "图", "表", "摘要", "Abstract", "Normal", "Title"])):
            md_lines.append(
                f"| {r['style_id']} | {r['name']} | {r['type']} | {r['alignment'] or ''} | "
                f"{r['font_size_pt'] or ''} | `{r['fonts']}` | `{r['spacing_twips']}` | `{r['indent_twips']}` |"
            )
    md_lines.extend([
        "",
        "## 4. 段落类别统计",
        "",
        "| 类别 | 数量 |",
        "|------|------|",
    ])
    for cls, count in summary["paragraph_class_counts"]:
        md_lines.append(f"| {cls} | {count} |")
    md_lines.extend([
        "",
        "## 5. 首页与正文前 40 个非空段落",
        "",
        "| # | 类别 | styleId | 格式 | 文本摘录 |",
        "|---|------|---------|------|----------|",
    ])
    for r in paragraph_records[:40]:
        fmt = {
            "jc": r["alignment"],
            "spacing": r["spacing_twips"],
            "ind": r["indent_twips"],
            "size": r["first_run_size_pt"],
        }
        md_lines.append(f"| {r['index']} | {r['class']} | {r['style_id']} | `{fmt}` | {r['text'][:80]} |")
    md_lines.extend([
        "",
        "## 6. 图表题注段落",
        "",
        "| # | 类型 | styleId | 对齐 | 段前/段后/行距 | 文本 |",
        "|---|------|---------|------|----------------|------|",
    ])
    for r in data["caption_paragraphs"]:
        md_lines.append(f"| {r['index']} | {r['class']} | {r['style_id']} | {r['alignment'] or ''} | `{r['spacing_twips']}` | {r['text'][:100]} |")
    md_lines.extend([
        "",
        "## 7. 参考文献段落",
        "",
        "| # | 类别 | styleId | 缩进 | 行距 | 文本摘录 |",
        "|---|------|---------|------|------|----------|",
    ])
    for r in data["reference_paragraphs"]:
        md_lines.append(f"| {r['index']} | {r['class']} | {r['style_id']} | `{r['indent_twips']}` | `{r['spacing_twips']}` | {r['text'][:100]} |")
    md_lines.extend([
        "",
        "## 8. 媒体与嵌入对象",
        "",
        f"- 媒体文件数：{len(media)}",
        f"- OLE 嵌入对象数：{len(embeddings)}",
        "",
        "完整机器可读定义见：`docs/format/jos_2025_docx_format_definitions.json`。",
        "",
    ])
    (OUT_DIR / "jos_2025_docx_format_definitions.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(json_path)
    print(OUT_DIR / "jos_2025_docx_format_definitions.md")


if __name__ == "__main__":
    main()
