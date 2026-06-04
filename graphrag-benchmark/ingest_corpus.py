"""
Ingests data/corpus.json into the running TigerGraph GraphRAG service.
Run AFTER the service is healthy (check with scripts/verify_tigergraph.py).
Supports resume via data/ingest_checkpoint.json and server-side dedup.
Round 2: retry wrapper, full-text paper support, final summary.
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


def save_checkpoint(index: int, success: int, failed: int, skipped: int):
    """Persist ingest progress."""
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "last_index": index,
            "success": success,
            "failed": failed,
            "skipped": skipped,
        }, f)


def post_with_retry(url: str, payload: dict, max_retries: int = 3) -> requests.Response:
    """POST with exponential backoff retries."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Retry {attempt+1}/{max_retries}: {e}")
                time.sleep(5 * (attempt + 1))
            else:
                raise


def fetch_ingested_ids() -> set:
    """Try to fetch already-ingested document IDs from the GraphRAG service."""
    try:
        r = requests.get(f"{BASE_URL}/v1/documents", timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return {doc.get("id", doc.get("paper_id", "")) for doc in data}
            if isinstance(data, dict) and "documents" in data:
                return {doc.get("id", doc.get("paper_id", "")) for doc in data["documents"]}
    except Exception:
        pass
    return set()


def build_payload(doc: dict) -> dict:
    """Build ingestion payload, supporting both Round 1 (abstract-only) and Round 2 (full-text) corpus formats."""
    # Round 2 format: has "text" field with full body text
    if "text" in doc:
        text = doc["text"]
        metadata = doc.get("metadata", {})
        return {
            "text": text,
            "metadata": {
                "id": metadata.get("paper_id", doc.get("id", "")),
                "title": doc.get("title", ""),
                "journal": metadata.get("journal", ""),
                "publish_time": metadata.get("publish_time", ""),
                "source": metadata.get("source", "fulltext"),
            },
        }
    # Round 1 format: has "id", "title", "abstract"
    return {
        "text": f"{doc['title']}\n\n{doc['abstract']}",
        "metadata": {
            "id": doc["id"],
            "title": doc["title"],
            "journal": doc.get("journal", ""),
            "publish_time": doc.get("publish_time", ""),
        },
    }


def get_doc_id(doc: dict) -> str:
    """Extract document ID from either corpus format."""
    if "metadata" in doc and isinstance(doc["metadata"], dict):
        return doc["metadata"].get("paper_id", "")
    return doc.get("id", "")


def ingest_document(doc: dict) -> bool:
    """POST one document with retries; try multiple endpoint paths."""
    payload = build_payload(doc)
    for endpoint in ENDPOINTS:
        try:
            post_with_retry(f"{BASE_URL}{endpoint}", payload)
            return True
        except Exception:
            continue
    return False


def main():
    """Ingest corpus with progress bar, resume, retry, and deduplication."""
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

    print(f"Corpus loaded: {len(corpus):,} documents")

    # Resume from checkpoint
    start_idx = load_checkpoint() + 1
    if start_idx > 0:
        print(f"Resuming from document {start_idx + 1}/{len(corpus)}")

    # Fetch already-ingested IDs for server-side dedup
    print("Checking for already-ingested documents...")
    ingested_ids = fetch_ingested_ids()
    if ingested_ids:
        print(f"  Found {len(ingested_ids):,} already-ingested documents on server")
    else:
        print("  No existing documents found (or endpoint not available)")

    success = 0
    failed = 0
    skipped = 0

    for i, doc in enumerate(tqdm(corpus, desc="Ingesting documents", unit="doc")):
        if i < start_idx:
            skipped += 1
            continue

        doc_id = get_doc_id(doc)
        if doc_id and doc_id in ingested_ids:
            skipped += 1
            continue

        if ingest_document(doc):
            success += 1
        else:
            failed += 1
        time.sleep(0.1)

        if (i + 1) % 500 == 0:
            save_checkpoint(i, success, failed, skipped)
            print(f"\nCheckpoint: {success} ok, {failed} failed, {skipped} skipped")

    save_checkpoint(len(corpus) - 1, success, failed, skipped)

    # Final summary
    print(f"\n{'='*50}")
    print(f"Ingestion complete")
    print(f"  Succeeded : {success:,}")
    print(f"  Skipped   : {skipped:,}")
    print(f"  Failed    : {failed:,}")
    print(f"  Total     : {len(corpus):,}")
    print(f"{'='*50}")
    if failed:
        print("Run scripts/verify_tigergraph.py to confirm retrieval works.")


if __name__ == "__main__":
    main()
