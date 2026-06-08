import sys
import os
from pathlib import Path

# Add MCP server path
mcp_dir = Path("/home/ros/work/p3-microservice/.agent/mcp-servers/scholar-downloader")
if str(mcp_dir) not in sys.path:
    sys.path.insert(0, str(mcp_dir))

from server import download_project_missing

print("Starting download process (with Sci-Hub and Playwright)...")
result = download_project_missing(output_dir="data/papers", use_scihub=True, playwright_fallback=True)
print("\n=== Download Result ===")
print(result)
