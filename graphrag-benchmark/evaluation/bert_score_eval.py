"""BERTScore computation for answer accuracy against ground truth."""

from evaluate import load

bertscore = load("bertscore")


def compute_bertscore(predictions: list[str], references: list[str]) -> dict:
    """
    Compute BERTScore precision, recall, and F1 for prediction/reference pairs.

    Args:
        predictions: Generated answers.
        references: Ground truth answers.

    Returns:
        Dict with per-item scores and mean_f1.
    """
    try:
        results = bertscore.compute(
            predictions=predictions,
            references=references,
            lang="en",
            model_type="distilbert-base-uncased",
        )
    except Exception as e:
        print(f"BERTScore error: {e}")
        n = len(predictions)
        return {
            "precision": [0.0] * n,
            "recall": [0.0] * n,
            "f1": [0.0] * n,
            "mean_f1": 0.0,
            "hashcode": "",
        }

    mean_f1 = sum(results["f1"]) / len(results["f1"]) if results["f1"] else 0.0

    return {
        "precision": results["precision"],
        "recall": results["recall"],
        "f1": results["f1"],
        "mean_f1": round(mean_f1, 4),
        "hashcode": results.get("hashcode", ""),
    }
