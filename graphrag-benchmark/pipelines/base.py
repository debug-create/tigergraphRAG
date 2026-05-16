"""Base pipeline with shared Gemini calls and token/latency tracking."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key or _api_key.startswith("your_"):
    print("WARNING: GEMINI_API_KEY not set. Copy .env.example to .env and add your key.")

# Default from env; fallbacks used if quota/model unavailable (e.g. 2.0-flash limit 0 on some keys)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_MODEL_FALLBACKS = ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest")


class BasePipeline:
    """
    Shared base for all three pipelines.
    Handles Gemini calls and token + latency tracking.
    """

    def __init__(self, name: str):
        """
        Initialize pipeline with a display name.

        Args:
            name: Human-readable pipeline label.
        """
        self.name = name
        self.client = genai.Client(api_key=_api_key)

    def call_llm(self, prompt: str) -> dict:
        """
        Call Gemini 2.0 Flash and return answer with usage metadata.

        Args:
            prompt: Full prompt string.

        Returns:
            Dict with answer, input_tokens, output_tokens, total_tokens, latency_seconds.
        """
        start = time.time()
        models_to_try = [GEMINI_MODEL] + [m for m in GEMINI_MODEL_FALLBACKS if m != GEMINI_MODEL]
        last_error = None

        try:
            response = None
            for model_id in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_id,
                        contents=prompt,
                    )
                    if model_id != GEMINI_MODEL:
                        print(f"  [{self.name}] using fallback model: {model_id}")
                    break
                except Exception as e:
                    last_error = e
                    err = str(e)
                    if "404" in err or "429" in err or "NOT_FOUND" in err or "RESOURCE_EXHAUSTED" in err:
                        continue
                    raise

            if response is None:
                raise last_error or RuntimeError("No Gemini model available")

            latency = time.time() - start
            usage = response.usage_metadata
            answer = response.text or ""

            time.sleep(1)

            return {
                "answer": answer,
                "input_tokens": usage.prompt_token_count or 0,
                "output_tokens": usage.candidates_token_count or 0,
                "total_tokens": usage.total_token_count or 0,
                "latency_seconds": round(latency, 3),
            }
        except Exception as e:
            print(f"Gemini API error in {self.name}: {e}")
            time.sleep(1)
            return {
                "answer": f"[Error: {e}]",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "latency_seconds": round(time.time() - start, 3),
            }

    def query(self, question: str) -> dict:
        """
        Run a question through the pipeline. Override in subclasses.

        Args:
            question: User question text.

        Returns:
            Pipeline result dict including pipeline name and context fields.
        """
        raise NotImplementedError
