"""
Analyse FAIL verdicts from the LLM judge for pipeline1 (LLM-Only).
Prints question, ground truth, the actual answer, and the fail reason.
Saves full output to results/fail_analysis.txt.

Usage: python scripts/fix_ground_truth.py
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "questions.json"
RESULTS_PATH = ROOT / "results" / "benchmark_results.json"
OUTPUT_PATH = ROOT / "results" / "fail_analysis.txt"


def main():
    if not RESULTS_PATH.exists():
        print(f"ERROR: {RESULTS_PATH} not found. Run evaluation/run_benchmark.py first.")
        sys.exit(1)

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = {q["id"]: q for q in json.load(f)}

    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)

    lines = []
    fail_count = 0

    for r in results:
        qid = r["question_id"]
        q = questions.get(qid, {})

        p1 = r.get("pipeline1", {})
        verdict = p1.get("llm_judge", "N/A")
        if verdict != "FAIL":
            continue

        fail_count += 1
        sep = "=" * 72
        block = [
            sep,
            f"Q{qid} (Category {r.get('category', '?')}) — FAIL",
            sep,
            f"QUESTION:      {r.get('question', q.get('question', ''))}",
            f"GROUND TRUTH:  {q.get('ground_truth', r.get('ground_truth', ''))}",
            f"ACTUAL ANSWER: {p1.get('answer', '')}",
            f"FAIL REASON:   {p1.get('llm_judge_reason', p1.get('llm_judge', ''))}",
            "",
        ]
        lines.extend(block)
        for b in block:
            print(b)

    summary = f"\nTotal FAIL verdicts for pipeline1: {fail_count} / {len(results)}"
    print(summary)
    lines.append(summary)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
