"""
System tools

Provides system-level information.
"""

import sys
import psutil
import shutil
from typing import Dict, Any

def get_system_info(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = shutil.disk_usage(".")
        return {
            "success": True,
            "os": sys.platform,
            "cpu_percent": cpu_pct,
            "memory_percent": mem.percent,
            "disk_percent": round((disk.used / disk.total) * 100, 2)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
