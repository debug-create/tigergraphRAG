"""
Quick smoke test — run before the full benchmark.
Tests one question through Pipeline 1 and Pipeline 2.
Does NOT require TigerGraph. Catches 90% of issues early.
Run with: python tests/smoke_test.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def check_env():
    """Ensure Gemini API key is configured."""
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key.startswith("your_"):
        raise RuntimeError("GEMINI_API_KEY not set in .env")


def test_pipeline1():
    """Smoke test LLM-only pipeline."""
    from pipelines.pipeline1_llm_only import LLMOnlyPipeline

    p = LLMOnlyPipeline()
    result = p.query("What is the ACE2 receptor?")
    assert isinstance(result["answer"], str) and len(result["answer"]) > 20
    assert result["total_tokens"] > 0, f"Got 0 tokens — check API key/quota: {result['answer'][:200]}"
    assert result["latency_seconds"] >= 0
    assert not result["answer"].startswith("[Error:")
    print(f"[OK] Pipeline 1 — {result['total_tokens']} tokens, {result['latency_seconds']}s")
    print(f"   Answer preview: {result['answer'][:100]}...")
    return result


def test_pipeline2():
    """Smoke test Basic RAG pipeline."""
    from pipelines.pipeline2_basic_rag import BasicRAGPipeline

    corpus = ROOT / "data" / "corpus.json"
    if not corpus.exists():
        raise FileNotFoundError("data/corpus.json missing — run: python data/download_corpus.py")

    print("Loading Pipeline 2 (takes ~3-5 min for first embedding)...")
    p = BasicRAGPipeline(corpus_path=str(corpus), top_k=5)
    result = p.query("What is the ACE2 receptor?")
    assert isinstance(result["answer"], str) and len(result["answer"]) > 20
    assert result["total_tokens"] > 0, f"Got 0 tokens: {result['answer'][:200]}"
    assert not result["answer"].startswith("[Error:")
    print(f"[OK] Pipeline 2 — {result['total_tokens']} tokens, {result['latency_seconds']}s")
    print(f"   Answer preview: {result['answer'][:100]}...")
    return result


if __name__ == "__main__":
    print("=== Smoke Test ===\n")
    check_env()
    r1 = test_pipeline1()
    r2 = test_pipeline2()
    print(f"\nP1 tokens: {r1['total_tokens']} | P2 tokens: {r2['total_tokens']}")
    print("Note: Basic RAG uses MORE tokens than LLM-Only (expected — context is added)")
    print("GraphRAG should use FEWER tokens than Basic RAG (that's the win)")
