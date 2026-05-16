"""
Validate environment and project files before running benchmarks.
Usage: python scripts/check_setup.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REQUIRED_ENV = [
    "GEMINI_API_KEY",
    "HF_TOKEN",
    "TIGERGRAPH_GRAPHRAG_URL",
]
OPTIONAL_ENV = [
    "TIGERGRAPH_HOST",
    "TIGERGRAPH_USERNAME",
    "TIGERGRAPH_PASSWORD",
    "TIGERGRAPH_GRAPHNAME",
]


def check_env():
    """Load .env and verify required keys are set."""
    from dotenv import load_dotenv

    env_path = ROOT / ".env"
    if not env_path.exists():
        print("[FAIL] .env not found - copy .env.example to .env and fill in keys")
        return False

    load_dotenv(env_path)
    ok = True
    for key in REQUIRED_ENV:
        val = os.getenv(key, "")
        if not val or val.startswith("your_"):
            print(f"[FAIL] {key} missing or still a placeholder")
            ok = False
        else:
            print(f"[OK] {key} is set")

    for key in OPTIONAL_ENV:
        val = os.getenv(key, "")
        if val and not val.startswith("your_"):
            print(f"[OK] {key} is set")
        else:
            print(f"[WARN] {key} not set (optional unless using Savanna directly)")

    return ok


def check_files():
    """Verify required project files exist."""
    paths = [
        ROOT / "data" / "questions.json",
        ROOT / "requirements.txt",
        ROOT / "pipelines" / "base.py",
        ROOT / "evaluation" / "run_benchmark.py",
    ]
    ok = True
    for p in paths:
        if p.exists():
            print(f"[OK] {p.relative_to(ROOT)}")
        else:
            print(f"[FAIL] Missing {p.relative_to(ROOT)}")
            ok = False

    corpus = ROOT / "data" / "corpus.json"
    if corpus.exists():
        print(f"[OK] data/corpus.json ({corpus.stat().st_size // 1024} KB)")
    else:
        print("[WARN] data/corpus.json missing - run: python data/download_corpus.py")

    return ok


def check_questions():
    """Validate questions.json has 30 items in categories A/B/C."""
    path = ROOT / "data" / "questions.json"
    with open(path, encoding="utf-8") as f:
        qs = json.load(f)
    if len(qs) != 30:
        print(f"[FAIL] Expected 30 questions, found {len(qs)}")
        return False
    cats = {q.get("category") for q in qs}
    for c in ("A", "B", "C"):
        n = sum(1 for q in qs if q.get("category") == c)
        if n != 10:
            print(f"[FAIL] Category {c}: expected 10 questions, found {n}")
            return False
    print("[OK] questions.json: 30 questions (10 per category A/B/C)")
    return True


def main():
    print("=== Setup Check ===\n")
    files_ok = check_files()
    print()
    questions_ok = check_questions()
    print()
    env_ok = check_env()
    print()
    if files_ok and questions_ok and env_ok:
        print("[OK] Setup looks good. Next: python data/download_corpus.py")
        return 0
    print("[FAIL] Fix issues above before running the benchmark.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
