"""
File tools

Provides read-only access to files and directory scanning.
"""

import os
from typing import Dict, Any

def list_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", ".")
    try:
        entries = os.listdir(path)
        files = [f for f in entries if os.path.isfile(os.path.join(path, f))]
        dirs = [d for d in entries if os.path.isdir(os.path.join(path, d))]
        return {
            "success": True,
            "path": os.path.abspath(path),
            "files": files[:100], # Limit output
            "directories": dirs[:100]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_file_content(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path", "")
    if not path:
        return {"success": False, "error": "Path is required"}
    try:
        # Prevent reading files outside the project dir
        abs_path = os.path.abspath(path)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if not abs_path.startswith(project_root):
            return {"success": False, "error": "Security block: access denied outside project workspace"}
            
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(5000) # read up to 5k chars
        return {
            "success": True,
            "path": abs_path,
            "content": content,
            "truncated": len(content) >= 5000
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
