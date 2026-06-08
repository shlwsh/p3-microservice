import json
import time
from pathlib import Path
import sys

# add path to download_lib
sys.path.insert(0, str(Path("/home/ros/work/p3-microservice/.agent/mcp-servers/scholar-downloader")))
from download_lib import PaperItem, try_scihub_scidownl, try_scihub_http

def main():
    manifest_path = Path("data/papers/cited_papers_manifest.json")
    if not manifest_path.exists():
        print("Manifest not found")
        return
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    failed_keys = []
    
    # 过滤出 snapshot 的
    entries = manifest.get("entries", manifest)
    snapshot_items = {k: v for k, v in entries.items() if isinstance(v, dict) and v.get("archive_status") == "snapshot"}
    print(f"Found {len(snapshot_items)} snapshot items to check.")
    
    for key, data in snapshot_items.items():
        doi = data.get("doi", "")
        if not doi:
            print(f"[{key}] No DOI, definitely failed.")
            failed_keys.append(key)
            continue
            
        item = PaperItem(citeKey=key, doi=doi, title=data.get("title", ""), author="", year="")
        # Fast try scihub (no playwright)
        dest = Path("data/papers") / f"{key}_test.pdf"
        
        ok = False
        try:
            ok = try_scihub_http(item, str(dest))
            if not ok:
                ok = try_scihub_scidownl(item, str(dest))
        except Exception as e:
            print(f"[{key}] Error: {e}")
            
        if ok:
            print(f"[{key}] ✅ SciHub Success")
            dest.unlink(missing_ok=True) # delete test file since we'll do real replace later or keep it? We just want to know if it's possible.
        else:
            print(f"[{key}] ❌ SciHub Failed")
            failed_keys.append(key)
            
    print("\n=== Failed Keys ===")
    print(json.dumps(failed_keys, indent=2))
    
    with open("failed_keys.json", "w") as f:
        json.dump(failed_keys, f)

if __name__ == "__main__":
    main()
