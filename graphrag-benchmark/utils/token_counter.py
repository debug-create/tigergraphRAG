"""tiktoken-based token counter for corpus verification and offline estimates."""

import tiktoken


def get_encoder(model: str = "cl100k_base"):
    """
    Return a tiktoken encoding instance.

    Args:
        model: Encoding name (cl100k_base matches GPT-4/Gemini-style counting).

    Returns:
        tiktoken.Encoding instance.
    """
    return tiktoken.get_encoding(model)


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count tokens in a single string.

    Args:
        text: Input text to tokenize.
        model: Encoding name.

    Returns:
        Integer token count.
    """
    enc = get_encoder(model)
    return len(enc.encode(text))


def count_tokens_batch(texts: list[str], model: str = "cl100k_base") -> int:
    """
    Count total tokens across a list of strings.

    Args:
        texts: List of strings.
        model: Encoding name.

    Returns:
        Sum of token counts.
    """
    return sum(count_tokens(t, model) for t in texts)
