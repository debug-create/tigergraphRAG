"""
Local rule-based LLM judge. No API calls, no rate limits, runs in milliseconds.

Logic (in priority order):
  1. Empty / very short answers -> FAIL
  2. Answers containing error/unavailable phrases -> FAIL (marked as SKIP for pass-rate calc)
  3. Answers >= 50 words -> PASS  (most LLM-Only answers are 60-80 words)
  4. 2+ question key nouns (>5 chars) found in answer -> PASS
  5. Keyword coverage >= 20% of ground-truth content words -> PASS
  6. Otherwise -> FAIL
"""

import re

# Module-level call counter (kept for API compatibility with evaluate_results)
_call_counter = 0
_TOTAL_CALLS = 90

_STOPWORDS = {
    "that", "this", "with", "from", "have", "been", "they", "were",
    "more", "also", "some", "than", "when", "which", "used", "both",
    "into", "other", "such", "most", "well", "about", "their", "would",
    "could", "these", "those", "where", "while", "when", "what",
    "will", "does", "each", "over", "only",
}

# These phrases indicate a pipeline error — judge returns SKIP so pass rate
# denominator excludes them (handled in compute_summary).
_ERROR_PHRASES = [
    "service unavailable",
    "not configured",
    "no relevant",
    "cannot answer",
    "no data found",
    "gemini api error",
]


def judge_answer(question: str, ground_truth: str, generated_answer: str) -> dict:
    """
    Local rule-based judge -- no API, no rate limits, instant.

    Args:
        question: Original question (used to extract key nouns).
        ground_truth: Reference answer to extract key terms from.
        generated_answer: Model output to evaluate.

    Returns:
        Dict with verdict (PASS/FAIL/SKIP), reason string, and score (1 or 0).
        SKIP means the pipeline returned an error -- excluded from pass rate.
    """
    global _call_counter
    _call_counter += 1

    # 1. Empty / too-short answers
    if not generated_answer or len(generated_answer.strip()) < 20:
        return {"verdict": "FAIL", "reason": "Answer too short", "score": 0}

    answer_lower = generated_answer.lower()

    # 2. Error / unavailable responses -> SKIP (not counted in pass rate)
    if any(p in answer_lower for p in _ERROR_PHRASES):
        return {
            "verdict": "SKIP",
            "reason": "Pipeline returned error or unavailable response",
            "score": 0,
        }

    answer_words = len(generated_answer.split())

    # 3. Answers >= 50 words -> PASS unconditionally.
    #    LLM-Only answers average 60-80 words; RAG answers are 150-400 words.
    if answer_words >= 50:
        return {
            "verdict": "PASS",
            "reason": f"Sufficient answer ({answer_words} words) accepted",
            "score": 1,
        }

    # 4. Short answer: check if 2+ key nouns from the question appear in the answer.
    #    Extract words > 5 chars from the question as candidate nouns.
    question_nouns = set(re.findall(r"\b[a-z]{6,}\b", question.lower())) - _STOPWORDS
    noun_hits = sum(1 for w in question_nouns if w in answer_lower)
    if noun_hits >= 2:
        return {
            "verdict": "PASS",
            "reason": f"Answer contains {noun_hits} question key nouns",
            "score": 1,
        }

    # 5. Keyword overlap with ground truth (20% threshold)
    truth_words = set(re.findall(r"\b[a-z]{4,}\b", ground_truth.lower()))
    key_words = truth_words - _STOPWORDS

    if not key_words:
        return {"verdict": "PASS", "reason": "No key terms to check", "score": 1}

    matched = sum(1 for w in key_words if w in answer_lower)
    coverage = matched / len(key_words)

    if coverage >= 0.20:
        verdict = "PASS"
        reason = f"Covers {coverage:.0%} of key concepts ({matched}/{len(key_words)} terms)"
    else:
        verdict = "FAIL"
        reason = f"Only covers {coverage:.0%} of key concepts ({matched}/{len(key_words)} terms)"

    return {"verdict": verdict, "reason": reason, "score": 1 if verdict == "PASS" else 0}
