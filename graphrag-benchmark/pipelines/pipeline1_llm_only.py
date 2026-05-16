"""Pipeline 1: LLM-only baseline with no retrieval."""

from pipelines.base import BasePipeline


class LLMOnlyPipeline(BasePipeline):
    """Sends questions directly to Gemini without any corpus retrieval."""

    def __init__(self):
        super().__init__("LLM-Only")

    def query(self, question: str) -> dict:
        """
        Answer using model knowledge only (worst-case token baseline).

        Args:
            question: Biomedical question.

        Returns:
            Result dict with answer, tokens, and zero context.
        """
        prompt = f"""Answer the following question based on your knowledge about COVID-19 and biomedical research.
Be concise and accurate.

Question: {question}

Answer:"""

        result = self.call_llm(prompt)
        result["pipeline"] = self.name
        result["context_used"] = None
        result["context_tokens"] = 0
        return result
