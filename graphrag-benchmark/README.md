# GraphRAG Inference Benchmark

## Running the Full Stack

### Option A: Dashboard + API (recommended for demo)
```bash
# Terminal 1 — Python API
cd graphrag-benchmark
.venv\Scripts\activate
uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — Next.js dashboard  
cd medi-graph-dashboard
pnpm dev
```
Open http://localhost:3000

### Option B: Streamlit only
```bash
cd graphrag-benchmark
streamlit run dashboard/app.py
```
Open http://localhost:8501

---

Prove that **GraphRAG** reduces LLM token consumption while maintaining answer accuracy vs vanilla RAG and LLM-only pipelines on the CORD-19 biomedical corpus.

## Stack (all free)

| Tool | Purpose |
|------|---------|
| Gemini 2.5 Flash | LLM for all 3 pipelines |
| sentence-transformers | Local embeddings (MiniLM) |
| ChromaDB | Persistent vector store (data/chroma_index) |
| TigerGraph GraphRAG | Graph retrieval service |
| BERTScore | Local accuracy metric |
| Llama 3.1 8B (HF API) | LLM-as-Judge |
| Streamlit | Comparison dashboard |

## Prerequisites

- Python 3.10+
- [Google AI Studio](https://aistudio.google.com/) API key (`GEMINI_API_KEY`)
- [HuggingFace token](https://huggingface.co/settings/tokens) (`HF_TOKEN`)
- TigerGraph GraphRAG service for Pipeline 3 ([repo](https://github.com/tigergraph/graphrag))

## Setup (clean virtual environment)

```bash
cd graphrag-benchmark
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env`:

```env
GEMINI_API_KEY=...
HF_TOKEN=...
TIGERGRAPH_GRAPHRAG_URL=http://localhost:8000
TIGERGRAPH_HOST=...
TIGERGRAPH_USERNAME=tigergraph
TIGERGRAPH_PASSWORD=...
TIGERGRAPH_GRAPHNAME=GraphRAG
```

Validate setup:

```bash
python scripts/check_setup.py
```

## Run order

### 1. Download corpus (~2M tokens)

```bash
python data/download_corpus.py
```

Expect: `Status: ✅ PASS` with ≥2,000,000 tokens.

If download fails, place `metadata.csv` in `data/` and re-run (uses cache).

### 2. Smoke test (Pipeline 1 + 2)

```bash
python tests/smoke_test.py
```

### 3. TigerGraph GraphRAG (Pipeline 3)

```bash
git clone https://github.com/tigergraph/graphrag
cd graphrag && cp .env.example .env
# Add GEMINI_API_KEY, then:
docker-compose up -d
```

From benchmark repo:

```bash
python scripts/verify_tigergraph.py
python ingest_corpus.py
python scripts/verify_tigergraph.py
```

### 4. Full benchmark (30 questions × 3 pipelines)

```bash
python evaluation/run_benchmark.py
```

- Saves after **each question** to `results/benchmark_results.json`
- Resumes on crash (skips completed question IDs)
- Run a single pipeline: `python evaluation/run_benchmark.py --pipeline 1` (1, 2, or 3)
- Re-evaluate only: `python evaluation/run_benchmark.py --evaluate-only`

### 5. Blog post from results

```bash
python scripts/fill_blog_post.py
```

### 6. Dashboard

```bash
streamlit run dashboard/app.py
```

1. Click **Load pipelines** (first time ~5 min for embeddings)
2. Run preset Category A then Category C questions for demo
3. Open **Benchmark Results** tab after full benchmark

## Project layout

See `PROJECT_CONTEXT.md` for full architecture and constraints.

## Metrics

| Metric | Source |
|--------|--------|
| Tokens | Gemini `usage_metadata` |
| BERTScore F1 | Local `distilbert-base-uncased` |
| LLM Judge | Llama-3.1-8B via HuggingFace |
| Cost | `utils/cost_calculator.py` |

**Targets:** GraphRAG pass rate ≥90%, BERTScore F1 ≥0.55, token reduction vs Basic RAG on Category C.

## Submission files

- `results/benchmark_report.md` — auto-generated
- `BLOG_POST.md` — fill via `scripts/fill_blog_post.py`
- `TODO.md` — checklist
- Demo video (5–7 min) using dashboard

## License

TigerGraph GraphRAG Inference Hackathon submission.
