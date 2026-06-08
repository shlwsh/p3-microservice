import os
import re
from pathlib import Path

workspace = Path("/home/ros/work/p3-microservice")
mcp_dir = workspace / ".agent/mcp-servers/scholar-downloader"

# Patch download_lib.py
lib_path = mcp_dir / "download_lib.py"
lib_code = lib_path.read_text()

lib_code = lib_code.replace('ROOT.parents[2] / "doctor" / "paper1" / "data" / "papers"', 'ROOT.parents[2] / "data" / "papers"')
lib_code = lib_code.replace('DEFAULT_CONFIG = ROOT / "config" / "paper1_missing.json"', 'DEFAULT_CONFIG = ROOT.parents[2] / "data" / "papers" / "cited_papers_manifest.json"')

# Add author and year to PaperItem
lib_code = lib_code.replace('openUrl: str | None = None', 'author: str = ""\n    year: str = ""\n    openUrl: str | None = None')

# Fix dest_path_for
dest_path_func = """def dest_path_for(output_dir: Path, paper: PaperItem) -> Path:
    author = "unknown"
    if paper.author:
        first = re.split(r"\\s+and\\s+", paper.author, maxsplit=1)[0]
        parts = first.replace(",", " ").split()
        author = re.sub(r"[^\\w]", "", parts[-1] if parts else "unknown")[:20]
    year = paper.year or "nodate"
    filename = f"{year}_{author}_{paper.citeKey}.pdf"
    return output_dir / filename"""
lib_code = re.sub(r"def dest_path_for\(output_dir: Path, paper: PaperItem\) -> Path:.*?return output_dir / f\"\{paper\.citeKey\}\.pdf\"", dest_path_func, lib_code, flags=re.DOTALL)

lib_path.write_text(lib_code)

# Patch server.py
srv_path = mcp_dir / "server.py"
srv_code = srv_path.read_text()

srv_code = srv_code.replace('doctor/paper1/data/papers', 'data/papers')
srv_code = srv_code.replace('download_paper1_missing', 'download_project_missing')
srv_code = srv_code.replace('8 missing paper1 references', 'missing project references')
srv_code = srv_code.replace('doctor/paper1/scripts/paper1_audit_papers.py', 'scripts/verify_cited_papers.py')

# Fix load_paper_config usage to read from verify_cited_papers.py
new_missing_logic = """
    # Read from references.bib
    scripts_dir = str(ROOT.parents[2] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    try:
        from verify_cited_papers import parse_bib, cited_keys, DEFAULT_BIB, DEFAULT_SECTIONS
        bib = parse_bib(DEFAULT_BIB)
        cited = cited_keys(DEFAULT_SECTIONS)
    except ImportError as e:
        return f"❌ Failed to import verify_cited_papers: {e}"
        
    papers = []
    for key in cited:
        if key in bib:
            e = bib[key]
            if e.doi:
                papers.append(PaperItem(
                    citeKey=e.key,
                    doi=e.doi,
                    title=e.title,
                    author=e.author,
                    year=e.year,
                    openUrl=e.url
                ))
"""
srv_code = re.sub(r'papers = load_paper_config\(DEFAULT_CONFIG\)', new_missing_logic.strip(), srv_code)
srv_path.write_text(srv_code)

# Patch README.md
readme_path = mcp_dir / "README.md"
readme_code = readme_path.read_text()
readme_code = readme_code.replace('doctor/paper1/data/papers', 'data/papers')
readme_code = readme_code.replace('doctor/paper1', 'p3-microservice')
readme_code = readme_code.replace('paper1', 'p3_microservice')
readme_path.write_text(readme_code)

print("Patching complete!")
