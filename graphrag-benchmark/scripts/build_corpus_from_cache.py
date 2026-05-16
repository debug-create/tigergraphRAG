"""
Build data/corpus.json from cached data/metadata.csv (skips bad CSV rows).
Run: .\.venv\Scripts\python scripts\build_corpus_from_cache.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
script = ROOT / "data" / "download_corpus.py"

if __name__ == "__main__":
    if not (ROOT / "data" / "metadata.csv").exists():
        print("Missing data/metadata.csv")
        sys.exit(1)
    sys.exit(subprocess.call([sys.executable, str(script), "--cache-only"], cwd=ROOT))
