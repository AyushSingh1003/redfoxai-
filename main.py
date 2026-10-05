"""
Root entrypoint for REDFOX AI FastAPI application.
Enables running `uvicorn main:app --reload` or `python main.py` directly from the repository root.
"""
import os
import sys
from pathlib import Path

# Resolve root and backend directories
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

# Ensure Python can find virtual environment site-packages if present
for site_pkg in BACKEND_DIR.glob(".venv/lib/python3.*/site-packages"):
    if site_pkg.is_dir() and str(site_pkg) not in sys.path:
        sys.path.insert(0, str(site_pkg))

# Ensure backend directory is in sys.path
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the FastAPI application from backend.main
import importlib.util

_spec = importlib.util.spec_from_file_location("backend_main", BACKEND_DIR / "main.py")
_backend_main = importlib.util.module_from_spec(_spec)
sys.modules["backend_main"] = _backend_main
_spec.loader.exec_module(_backend_main)

app = _backend_main.app

if __name__ == "__main__":
    import uvicorn
    reload_enabled = os.getenv("UVICORN_RELOAD", "1") == "1"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload_enabled)
