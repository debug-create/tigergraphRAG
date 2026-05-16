"""
Verify TigerGraph GraphRAG service is running and corpus is ingested.
Run this BEFORE running the full benchmark.
Usage: python scripts/verify_tigergraph.py
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")
BASE_URL = os.getenv("TIGERGRAPH_GRAPHRAG_URL", "http://localhost:8000").rstrip("/")


def check_health():
    """Check GET /health on GraphRAG service."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"✅ GraphRAG service is running at {BASE_URL}")
            return True
        print(f"[FAIL] Health check returned: {r.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to {BASE_URL}")
        print("")
        print("Docker not running. Use TigerGraph Savanna instead:")
        print("  1. Go to tgcloud.io and sign up (free, $60 credits)")
        print("  2. Create a new TigerGraph instance")
        print("  3. Follow tigergraph/graphrag README for Savanna setup")
        print("  4. Set TIGERGRAPH_GRAPHRAG_URL=https://your-instance.i.tgcloud.io")
        print("     in your .env file")
        return False


def check_corpus_ingested():
    """Try a test query to see if data is loaded."""
    try:
        payload = {"query": "What is ACE2?", "top_k": 3, "num_hops": 1}
        r = requests.post(f"{BASE_URL}/v1/retrieve", json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"✅ Corpus appears ingested — got response keys: {list(data.keys())}")
                print(f"   Sample response: {str(data)[:200]}...")
                return True
            print("⚠️  Service responded but returned empty — corpus may not be ingested yet")
            return False
        print(f"[FAIL] Retrieve endpoint: {r.status_code} -- {r.text[:200]}")
        return False
    except Exception as e:
        print(f"[FAIL] Error calling retrieve: {e}")
        return False


def test_full_query():
    """Test a full pipeline 3 query."""
    from pipelines.pipeline3_graphrag import GraphRAGPipeline

    p = GraphRAGPipeline()
    result = p.query("What is the role of ACE2 in SARS-CoV-2 infection?")
    print(f"✅ Pipeline 3 query OK — {result['total_tokens']} tokens")
    print(f"   Answer: {result['answer'][:150]}...")
    return result


def check_corpus_file():
    """Ensure benchmark corpus exists locally."""
    corpus = ROOT / "data" / "corpus.json"
    if corpus.exists():
        print(f"✅ Local corpus.json found ({corpus.stat().st_size // 1024} KB)")
        return True
    print("⚠️  data/corpus.json missing — run: python data/download_corpus.py")
    return False


if __name__ == "__main__":
    print("=== TigerGraph Verification ===\n")
    check_corpus_file()
    print()
    if check_health():
        if check_corpus_ingested():
            test_full_query()
        else:
            print("\nNext step: run 'python ingest_corpus.py' to ingest the corpus")
    else:
        print("\nSetup steps:")
        print("1. Clone: git clone https://github.com/tigergraph/graphrag")
        print("2. cd graphrag && cp .env.example .env")
        print("3. Add your GEMINI_API_KEY to that .env")
        print("4. docker-compose up -d")
        print("5. Wait 2 min, then re-run this script")
