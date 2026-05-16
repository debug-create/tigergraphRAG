"""
Fill BLOG_POST.md placeholders from benchmark_results.json or benchmark_report.md.
Usage: python scripts/fill_blog_post.py
"""

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "results" / "benchmark_results.json"
BLOG_PATH = ROOT / "BLOG_POST.md"


def load_stats():
    """Compute headline stats from benchmark results."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError("Run evaluation/run_benchmark.py first.")

    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)

    def stats(key):
        rows = [r[key] for r in results if key in r]
        return {
            "avg_tokens": statistics.mean(r["total_tokens"] for r in rows),
            "pass_rate": 100 * sum(1 for r in rows if r.get("llm_judge") == "PASS") / len(rows),
            "bert_f1": statistics.mean(r.get("bert_f1", 0) for r in rows),
        }

    p1, p2, p3 = stats("pipeline1"), stats("pipeline2"), stats("pipeline3")
    reduction = (p2["avg_tokens"] - p3["avg_tokens"]) / p2["avg_tokens"] * 100 if p2["avg_tokens"] else 0

    with open(ROOT / "data" / "corpus.json", encoding="utf-8") as f:
        corpus = json.load(f)

    return {
        "num_papers": len(corpus),
        "p1_tokens": f"{p1['avg_tokens']:.0f}",
        "p2_tokens": f"{p2['avg_tokens']:.0f}",
        "p3_tokens": f"{p3['avg_tokens']:.0f}",
        "p1_pass": f"{p1['pass_rate']:.1f}",
        "p2_pass": f"{p2['pass_rate']:.1f}",
        "p3_pass": f"{p3['pass_rate']:.1f}",
        "p1_bert": f"{p1['bert_f1']:.3f}",
        "p2_bert": f"{p2['bert_f1']:.3f}",
        "p3_bert": f"{p3['bert_f1']:.3f}",
        "reduction": f"{reduction:.1f}",
        "p3_pass_narrative": f"{p3['pass_rate']:.1f}",
        "p3_bert_narrative": f"{p3['bert_f1']:.3f}",
    }


def main():
    stats = load_stats()
    text = BLOG_PATH.read_text(encoding="utf-8")

    replacements = [
        (r"\[X\] biomedical research papers, \[X\]M tokens", f"{stats['num_papers']} biomedical research papers, 2M+ tokens"),
        (r"\| LLM-Only \| \[X\] \| \[X\]% \| \[X\] \| \$\[X\]", f"| LLM-Only | {stats['p1_tokens']} | {stats['p1_pass']}% | {stats['p1_bert']} | $0.00"),
        (r"\| Basic RAG \| \[X\] \| \[X\]% \| \[X\] \| \$\[X\]", f"| Basic RAG | {stats['p2_tokens']} | {stats['p2_pass']}% | {stats['p2_bert']} | $0.00"),
        (r"\| \*\*GraphRAG\*\* \| \*\*\[X\]\*\* \| \*\*\[X\]%\*\* \| \*\*\[X\]\*\* \| \*\*\$\[X\]\*\*",
         f"| **GraphRAG** | **{stats['p3_tokens']}** | **{stats['p3_pass']}%** | **{stats['p3_bert']}** | **$0.00**"),
        (r"\[X\]% vs Basic RAG", f"{stats['reduction']}% vs Basic RAG"),
        (r"\[X\]% answer accuracy", f"{stats['p3_pass_narrative']}% answer accuracy"),
        (r"BERTScore F1 of \[X\]", f"BERTScore F1 of {stats['p3_bert_narrative']}"),
        (r"Basic RAG retrieved \[X\] tokens", f"Basic RAG retrieved ~{stats['p2_tokens']} tokens"),
        (r"GraphRAG: \[X\] tokens", f"GraphRAG: ~{stats['p3_tokens']} tokens"),
        (r"Token delta: \[X\]% reduction", f"Token delta: {stats['reduction']}% reduction"),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, count=1)

    remaining = text.count("[X]")
    if remaining:
        print(f"⚠️  {remaining} [X] placeholders remain — edit BLOG_POST.md manually.")

    BLOG_PATH.write_text(text, encoding="utf-8")
    print(f"✅ Updated {BLOG_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
