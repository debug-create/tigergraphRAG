import json
from bert_score import score

with open('results/benchmark_results.json', encoding='utf-8') as f:
    results = json.load(f)

ground_truths = [q["ground_truth"] for q in results]
p1_answers = [q.get("pipeline1", {}).get("answer", "") for q in results]
p2_answers = [q.get("pipeline2", {}).get("answer", "") for q in results]
p3_answers = [q.get("pipeline3", {}).get("answer", "") for q in results]

def get_f1(candidates):
    P, R, F1 = score(
        candidates,
        ground_truths,
        model_type="roberta-large",
        lang="en",
        rescale_with_baseline=True,
        verbose=False
    )
    mean_f1 = sum(F1.tolist()) / len(F1)
    return mean_f1

f1_p1 = get_f1(p1_answers)
print(f"BERTScore F1 (LLM Only): {f1_p1:.4f}")

f1_p2 = get_f1(p2_answers)
print(f"BERTScore F1 (RAG): {f1_p2:.4f}")

f1_p3 = get_f1(p3_answers)
print(f"BERTScore F1 (GraphRAG): {f1_p3:.4f}")
