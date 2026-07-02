"""
Project tools

Provides automated checks for the overall codebase structure and project overview.
"""

import os
from typing import Dict, Any

def get_project_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        python_files = 0
        json_files = 0
        total_size = 0
        for root, dirs, files in os.walk(project_root):
            # Skip caches
            if "venv" in root or ".git" in root or "__pycache__" in root or ".pytest_cache" in root:
                continue
            for f in files:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
                if f.endswith(".py"):
                    python_files += 1
                elif f.endswith(".json"):
                    json_files += 1
                    
        return {
            "success": True,
            "project_root": project_root,
            "python_files_count": python_files,
            "json_files_count": json_files,
            "total_size_bytes": total_size
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
