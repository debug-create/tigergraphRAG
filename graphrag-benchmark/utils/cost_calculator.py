"""Token-to-USD cost calculator using Gemini 2.5 Flash pricing."""


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Compute estimated USD cost for a single Gemini 1.5 Flash call.

    Args:
        input_tokens: Prompt token count.
        output_tokens: Completion token count.

    Returns:
        Total cost in USD.
    """
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.300
    return input_cost + output_cost


def calculate_monthly_cost_at_scale(avg_tokens: int, queries_per_day: int) -> dict:
    """
    Extrapolate production-scale monthly cost from average tokens per query.

    Args:
        avg_tokens: Average total tokens per query.
        queries_per_day: Expected daily query volume.

    Returns:
        Dict with daily_cost_usd, monthly_cost_usd, queries_per_day.
    """
    input_ratio = 0.85
    input_tokens = avg_tokens * input_ratio
    output_tokens = avg_tokens * (1 - input_ratio)

    daily_cost = calculate_cost(input_tokens, output_tokens) * queries_per_day
    monthly_cost = daily_cost * 30

    return {
        "daily_cost_usd": round(daily_cost, 4),
        "monthly_cost_usd": round(monthly_cost, 2),
        "queries_per_day": queries_per_day,
    }
