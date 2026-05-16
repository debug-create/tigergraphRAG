"""
Ingests data/corpus.json into the running TigerGraph GraphRAG service.
Run AFTER the service is healthy (check with scripts/verify_tigergraph.py).
Supports resume via data/ingest_checkpoint.json.
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
BASE_URL = os.getenv("TIGERGRAPH_GRAPHRAG_URL", "http://localhost:8000").rstrip("/")
CHECKPOINT_PATH = ROOT / "data" / "ingest_checkpoint.json"
ENDPOINTS = ["/v1/documents", "/v1/ingest", "/ingest"]


def load_checkpoint() -> int:
    """Return index of last successfully ingested document."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            return int(json.load(f).get("last_index", -1))
    return -1


def save_checkpoint(index: int, success: int, failed: int):
    """Persist ingest progress."""
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_index": index, "success": success, "failed": failed}, f)


def ingest_document(doc: dict) -> bool:
    """POST one document; try multiple endpoint paths."""
    payload = {
        "text": f"{doc['title']}\n\n{doc['abstract']}",
        "metadata": {
            "id": doc["id"],
            "title": doc["title"],
            "journal": doc.get("journal", ""),
            "publish_time": doc.get("publish_time", ""),
        },
    }
    for endpoint in ENDPOINTS:
        try:
            r = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=30)
            if r.status_code in (200, 201):
                return True
        except requests.exceptions.RequestException:
            continue
    return False


def main():
    """Ingest corpus with progress bar and checkpoint resume."""
    corpus_path = ROOT / "data" / "corpus.json"
    if not corpus_path.exists():
        print("Run python data/download_corpus.py first.")
        return

    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code != 200:
            print(f"GraphRAG health failed: {r.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"Cannot reach GraphRAG at {BASE_URL}: {e}")
        return

    with open(corpus_path, encoding="utf-8") as f:
        corpus = json.load(f)

    start_idx = load_checkpoint() + 1
    if start_idx > 0:
        print(f"Resuming from document {start_idx + 1}/{len(corpus)}")

    success = 0
    failed = 0
    for i, doc in enumerate(tqdm(corpus, desc="Ingesting")):
        if i < start_idx:
            success += 1
            continue
        if ingest_document(doc):
            success += 1
        else:
            failed += 1
        time.sleep(0.1)
        if (i + 1) % 500 == 0:
            save_checkpoint(i, success, failed)
            print(f"\nCheckpoint: {success} ok, {failed} failed")

    save_checkpoint(len(corpus) - 1, success, failed)
    print(f"\nDone: {success} ingested, {failed} failed")
    if failed:
        print("Run scripts/verify_tigergraph.py to confirm retrieval works.")


if __name__ == "__main__":
    main()
