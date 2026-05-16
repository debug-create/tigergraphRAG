"""
Remove llm_judge and bert_f1 fields from all pipeline records in benchmark_results.json.
Run this before re-evaluating with a different judge model.
Usage: python scripts/clear_judge_scores.py
"""

import json
import pathlib
import sys

results_path = pathlib.Path("results/benchmark_results.json")

if not results_path.exists():
    print(f"ERROR: {results_path} not found. Run evaluation/run_benchmark.py first.")
    sys.exit(1)

with open(results_path, encoding="utf-8") as f:
    data = json.load(f)

cleared = 0
for r in data:
    for key in ["pipeline1", "pipeline2", "pipeline3"]:
        if key in r and isinstance(r[key], dict):
            removed = r[key].pop("llm_judge", None)
            r[key].pop("llm_judge_reason", None)
            r[key].pop("bert_f1", None)
            if removed is not None:
                cleared += 1

with open(results_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Cleared judge/bert scores from {cleared} pipeline records across {len(data)} questions.")
print("Ready to re-evaluate: python evaluation/run_benchmark.py --evaluate-only")
