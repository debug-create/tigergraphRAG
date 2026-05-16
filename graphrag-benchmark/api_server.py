"""
FastAPI server that bridges the Next.js frontend to the Python pipelines.
Run with: uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import time
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="MediGraph API", version="1.0.0")

# Allow Next.js dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load pipelines (only once, cached)
_pipelines = None

def get_pipelines():
    global _pipelines
    if _pipelines is None:
        from pipelines.pipeline1_llm_only import LLMOnlyPipeline
        from pipelines.pipeline2_basic_rag import BasicRAGPipeline
        from pipelines.pipeline3_graphrag import GraphRAGPipeline
        _pipelines = {
            "p1": LLMOnlyPipeline(),
            "p2": BasicRAGPipeline(corpus_path="data/corpus.json"),
            "p3": GraphRAGPipeline(),
        }
    return _pipelines


class QueryRequest(BaseModel):
    question: str


class PipelineResult(BaseModel):
    pipeline: str
    answer: str
    total_tokens: int
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    cost_usd: float
    llm_judge: str = "N/A"


class QueryResponse(BaseModel):
    question: str
    pipeline1: PipelineResult
    pipeline2: PipelineResult
    pipeline3: PipelineResult
    token_reduction_pct: float


@app.get("/health")
def health():
    return {"status": "ok", "service": "MediGraph API"}


@app.get("/pipelines/status")
def pipeline_status():
    """Check if pipelines are loaded without actually loading them."""
    return {
        "loaded": _pipelines is not None,
        "message": "Pipelines ready" if _pipelines else "Pipelines not loaded yet — call /pipelines/load first"
    }


@app.post("/pipelines/load")
def load_pipelines():
    """Pre-load all pipelines. Call this once on startup."""
    try:
        get_pipelines()
        return {"status": "ok", "message": "All pipelines loaded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    """Run all 3 pipelines on the question and return results."""
    pipelines = get_pipelines()
    
    results = {}
    for key, pipeline in pipelines.items():
        try:
            result = pipeline.query(req.question)
            results[key] = result
        except Exception as e:
            results[key] = {
                "pipeline": pipeline.name if hasattr(pipeline, 'name') else key,
                "answer": f"Pipeline error: {str(e)}",
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_seconds": 0.0,
                "cost_usd": 0.0,
            }
    
    # Calculate token reduction
    p2_tokens = results["p2"].get("total_tokens", 1)
    p3_tokens = results["p3"].get("total_tokens", 0)
    reduction = ((p2_tokens - p3_tokens) / p2_tokens * 100) if p2_tokens > 0 else 0
    
    def to_result(r):
        return PipelineResult(
            pipeline=r.get("pipeline", "unknown"),
            answer=r.get("answer", ""),
            total_tokens=r.get("total_tokens", 0),
            input_tokens=r.get("input_tokens", 0),
            output_tokens=r.get("output_tokens", 0),
            latency_seconds=r.get("latency_seconds", 0.0),
            cost_usd=r.get("cost_usd", 0.0),
            llm_judge=r.get("llm_judge", "N/A"),
        )
    
    return QueryResponse(
        question=req.question,
        pipeline1=to_result(results["p1"]),
        pipeline2=to_result(results["p2"]),
        pipeline3=to_result(results["p3"]),
        token_reduction_pct=round(reduction, 1),
    )


@app.get("/benchmark/results")
def get_benchmark_results():
    """Return the full benchmark results from benchmark_results.json."""
    results_path = pathlib.Path("results/benchmark_results.json")
    if not results_path.exists():
        return {"error": "No benchmark results found. Run: python evaluation/run_benchmark.py"}
    
    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)
    
    # Compute summary stats
    p1_tokens = [r["pipeline1"]["total_tokens"] for r in data if "pipeline1" in r]
    p2_tokens = [r["pipeline2"]["total_tokens"] for r in data if "pipeline2" in r]
    p3_tokens = [r["pipeline3"]["total_tokens"] for r in data if "pipeline3" in r]
    
    p1_pass = [r["pipeline1"].get("llm_judge") for r in data if "pipeline1" in r]
    p2_pass = [r["pipeline2"].get("llm_judge") for r in data if "pipeline2" in r]
    p3_pass = [r["pipeline3"].get("llm_judge") for r in data if "pipeline3" in r]
    
    def pass_rate(verdicts):
        valid = [v for v in verdicts if v in ("PASS", "FAIL")]
        if not valid:
            return 0
        return round(sum(1 for v in valid if v == "PASS") / len(valid) * 100, 1)
    
    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0
    
    p2_avg = avg(p2_tokens)
    p3_avg = avg(p3_tokens)
    reduction = round((p2_avg - p3_avg) / p2_avg * 100, 1) if p2_avg > 0 else 0
    
    return {
        "summary": {
            "token_reduction_pct": reduction,
            "pipeline1": {
                "avg_tokens": avg(p1_tokens),
                "pass_rate": pass_rate(p1_pass),
            },
            "pipeline2": {
                "avg_tokens": p2_avg,
                "pass_rate": pass_rate(p2_pass),
            },
            "pipeline3": {
                "avg_tokens": p3_avg,
                "pass_rate": pass_rate(p3_pass),
            },
        },
        "questions": data,
    }


@app.get("/questions/presets")
def get_preset_questions():
    """Return the 30 benchmark questions for the preset selector."""
    questions_path = pathlib.Path("data/questions.json")
    if not questions_path.exists():
        return []
    with open(questions_path, encoding="utf-8") as f:
        return json.load(f)
