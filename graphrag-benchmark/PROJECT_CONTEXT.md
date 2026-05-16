# GraphRAG Inference Benchmark — Full Project Context

> **Purpose of this file:** Paste this entire document into any LLM chat so it has complete context to work on this codebase without reading the repo first.

---

## 1. Project Summary

**Name:** GraphRAG Inference Benchmark (TigerGraph Hackathon submission)

**Location:** `graphrag-benchmark/` (workspace root: `tigergraph/graphrag-benchmark`)

**Goal:** Prove that **GraphRAG** reduces LLM token consumption while maintaining answer accuracy compared to:
1. **LLM-Only** (no retrieval)
2. **Basic RAG** (vector similarity + ChromaDB)
3. **GraphRAG** (TigerGraph knowledge graph traversal + structured context)

All three pipelines answer the **same 30 biomedical questions** on the **same CORD-19 corpus** (~2M tokens, ~4000 papers). Results are compared on tokens, latency, cost, BERTScore F1, and LLM-as-Judge pass rate.

**Core hypothesis:** GraphRAG uses 60–80% fewer tokens than Basic RAG on multi-hop (Category C) questions because it returns a focused subgraph instead of broad vector-retrieved chunks.

**Total API cost target:** $0 (free tiers only).

---

## 2. Hackathon & Submission Context

- **Event:** TigerGraph GraphRAG Inference Hackathon
- **Hashtag:** `#GraphRAGInferenceHackathon @TigerGraph`
- **Submission deliverables:**
  - GitHub repo with working code
  - `results/benchmark_report.md` (auto-generated after benchmark)
  - `BLOG_POST.md` (fill `[X]` placeholders from benchmark numbers)
  - Streamlit dashboard demo (5–7 min video script in Phase 2 prompt)
  - TigerGraph GraphRAG service integration (Pipeline 3)

**Bonus targets:**
- BERTScore mean F1 ≥ 0.55 (rescaled) or raw ≥ 0.88
- LLM-Judge pass rate ≥ 90% for GraphRAG

---

## 3. Strict Technology Rules (NEVER VIOLATE)

| Component | MUST use | NEVER use |
|-----------|----------|-----------|
| LLM (pipelines) | `gemini-1.5-flash-latest` via `google-generativeai` | OpenAI, Anthropic, Cohere |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) | OpenAI embeddings |
| Vector store | `chromadb` in-memory | Pinecone, Weaviate |
| LLM Judge | `meta-llama/Llama-3.1-8B-Instruct` via HuggingFace Inference API | Gemini for judge (saves quota) |
| BERTScore | `evaluate` + `bert-score`, `distilbert-base-uncased` (local) | — |
| Graph DB | TigerGraph Savanna + `tigergraph/graphrag` repo | — |
| Dashboard | Streamlit only | React, Vue, etc. |
| Dataset | CORD-19 biomedical corpus | — |

**Rate limiting:** `time.sleep(1)` after every Gemini API call (15 RPM free tier).

**Token counting for pipeline results:** Always use Gemini `response.usage_metadata` — NOT tiktoken estimates.

**Token counting for corpus verification:** Use tiktoken `cl100k_base` encoding.

---

## 4. Repository Structure

```
graphrag-benchmark/
├── .env                          # Secrets (gitignored) — GEMINI_API_KEY, HF_TOKEN, TigerGraph vars
├── .env.example                  # Template for env vars
├── .gitignore
├── requirements.txt
├── README.md
├── PROJECT_CONTEXT.md            # THIS FILE
├── BLOG_POST.md                  # Submission blog skeleton (fill after benchmark)
├── ingest_corpus.py              # Ingest corpus.json into TigerGraph GraphRAG service
│
├── data/
│   ├── download_corpus.py        # Download CORD-19 → corpus.json (≥2M tokens)
│   ├── metadata.csv              # Cached CSV (optional, gitignored if large)
│   ├── corpus.json               # Generated: [{id, title, abstract, authors, journal, publish_time}]
│   └── questions.json            # 30 test Qs with ground truth (categories A/B/C)
│
├── pipelines/
│   ├── __init__.py
│   ├── base.py                   # BasePipeline: Gemini calls + token tracking
│   ├── pipeline1_llm_only.py     # No retrieval
│   ├── pipeline2_basic_rag.py    # ChromaDB + sentence-transformers
│   └── pipeline3_graphrag.py     # TigerGraph GraphRAG REST + Gemini
│
├── evaluation/
│   ├── __init__.py
│   ├── bert_score_eval.py        # BERTScore F1
│   ├── llm_judge.py              # Llama-3.1-8B PASS/FAIL judge
│   └── run_benchmark.py          # Full 30×3 benchmark + report generation
│
├── dashboard/
│   └── app.py                    # Streamlit: Live Query + Benchmark Results tabs
│
├── results/
│   ├── benchmark_results.json    # Incremental JSON results (gitignored)
│   └── benchmark_report.md       # Auto-generated markdown report
│
├── scripts/
│   └── verify_tigergraph.py      # Health check + corpus ingest verification
│
├── tests/
│   └── smoke_test.py             # Quick P1+P2 test (no TigerGraph needed)
│
└── utils/
    ├── token_counter.py          # tiktoken for corpus verification
    └── cost_calculator.py        # Gemini Flash pricing → USD
```

---

## 5. Environment Variables

Copy `.env.example` → `.env`:

```env
GEMINI_API_KEY=your_key_here          # Google AI Studio — free tier
HF_TOKEN=your_huggingface_token_here  # huggingface.co/settings/tokens — for LLM judge
TIGERGRAPH_HOST=your_savanna_host     # Optional: Savanna direct access
TIGERGRAPH_USERNAME=tigergraph
TIGERGRAPH_PASSWORD=your_password
TIGERGRAPH_GRAPHNAME=GraphRAG
TIGERGRAPH_GRAPHRAG_URL=http://localhost:8000  # GraphRAG REST service URL
```

---

## 6. Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Same 30 Questions              │
                    │         (data/questions.json)          │
                    └────────────────────┬────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│  Pipeline 1     │           │  Pipeline 2     │           │  Pipeline 3     │
│  LLM-Only       │           │  Basic RAG      │           │  GraphRAG       │
│                 │           │                 │           │                 │
│  Question       │           │  Question       │           │  Question       │
│     ↓           │           │     ↓           │           │     ↓           │
│  Gemini Flash   │           │  Embed query    │           │  POST /v1/      │
│  (no context)   │           │     ↓           │           │  retrieve       │
│                 │           │  ChromaDB       │           │  (TigerGraph)   │
│                 │           │  top-5 chunks   │           │     ↓           │
│                 │           │     ↓           │           │  Structured     │
│                 │           │  Gemini Flash   │           │  graph context  │
│                 │           │  (+ context)    │           │     ↓           │
│                 │           │                 │           │  Gemini Flash   │
└────────┬────────┘           └────────┬────────┘           └────────┬────────┘
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │  evaluation/run_benchmark.py             │
                    │  • BERTScore (local)                     │
                    │  • LLM Judge (Llama via HF)              │
                    │  • results/benchmark_results.json        │
                    │  • results/benchmark_report.md           │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │  dashboard/app.py (Streamlit)            │
                    └─────────────────────────────────────────┘
```

**Shared corpus:** `data/corpus.json` — CORD-19 papers indexed by P2 (ChromaDB) and P3 (TigerGraph GraphRAG via `ingest_corpus.py`).

---

## 7. Data Layer

### 7.1 Corpus (`data/corpus.json`)

**Source:** CORD-19 metadata from AI2 Semantic Scholar.

**Download:** `python data/download_corpus.py`

**Process:**
1. Download metadata CSV (multiple S3 URLs with retries) OR HuggingFace `allenai/cord19` fallback
2. Filter: `abstract` not null, length > 100 chars
3. Take rows until ≥ **2,000,000 tokens** (tiktoken `cl100k_base`)
4. Default start: 4000 rows, expand by 1000 if under token threshold

**Record schema:**
```json
{
  "id": "cord_uid_value",
  "title": "Paper title",
  "abstract": "Full abstract text",
  "authors": "Author1, Author2",
  "journal": "Journal name",
  "publish_time": "2020-03-15"
}
```

**Verification:** End of `download_corpus.py` prints PASS/FAIL for ≥2M tokens.

### 7.2 Questions (`data/questions.json`)

**30 questions** in 3 categories (10 each):

| Category | Type | Expected behavior |
|----------|------|-------------------|
| **A** | Single-hop factual | LLM-Only, Basic RAG, GraphRAG similar accuracy; Basic RAG uses MORE tokens than LLM-Only |
| **B** | Two-hop relational | GraphRAG starts showing token advantage |
| **C** | Three-hop complex | GraphRAG should win dramatically on token reduction |

**Question schema:**
```json
{
  "id": 1,
  "category": "A",
  "question": "...",
  "ground_truth": "..."
}
```

**All 30 questions (abbreviated — full text in `data/questions.json`):**

**Category A (1–10):** COVID pneumonia symptoms; remdesivir mechanism; ICU admission %; SARS-CoV-2 incubation; ACE2 receptor; comorbidities; dexamethasone; cytokine storm; spike protein vs SARS-CoV-1; chest CT findings.

**Category B (11–20):** IL-6 inhibitors in trials; ACE2 and severity; influenza antivirals for SARS-CoV-2; blood type susceptibility; comorbidities + ACE2; SARS 2003 treatments repurposed; obesity and severity; MERS researchers → COVID vaccines; spike mutations transmissibility/vaccines; T-cells and long COVID.

**Category C (21–30):** Proteins targeted by COVID+cancer drugs; institutions ACE2+vaccine trials; SARS-CoV-2 → cardiac in diabetes; bat coronavirus antivirals; cytokines + autoimmune biologics repurposed; gut microbiome + immune + severity; Omicron spike mutations; dual-pathway drug trials; animal hosts + mutations + origin; complement + coagulation + therapeutics.

---

## 8. Pipelines (Detailed)

### 8.1 Base Pipeline (`pipelines/base.py`)

**Class:** `BasePipeline`

- Model: `genai.GenerativeModel("gemini-1.5-flash-latest")`
- `call_llm(prompt)` → `{answer, input_tokens, output_tokens, total_tokens, latency_seconds}`
- Uses `response.usage_metadata` for token counts
- `time.sleep(1)` after each call
- `query(question)` — abstract, implemented in subclasses

### 8.2 Pipeline 1 — LLM-Only (`pipelines/pipeline1_llm_only.py`)

**Class:** `LLMOnlyPipeline(BasePipeline)`

- Name: `"LLM-Only"`
- No retrieval; minimal prompt with question only
- Returns: `context_used=None`, `context_tokens=0`

### 8.3 Pipeline 2 — Basic RAG (`pipelines/pipeline2_basic_rag.py`)

**Class:** `BasicRAGPipeline(BasePipeline)`

- Name: `"Basic-RAG"`
- Embedder: `SentenceTransformer("all-MiniLM-L6-v2")`
- Vector store: `chromadb.Client()` in-memory, collection `"cord19"`, cosine space
- Chunking: 256 words, 32-word overlap
- Retrieval: `top_k=5` chunks
- First init: ~3–5 min to embed all chunks (progress bar via tqdm)
- Prompt: answer using ONLY provided context

### 8.4 Pipeline 3 — GraphRAG (`pipelines/pipeline3_graphrag.py`)

**Class:** `GraphRAGPipeline(BasePipeline)`

- Name: `"GraphRAG"`
- Base URL: `TIGERGRAPH_GRAPHRAG_URL` (default `http://localhost:8000`)

**Endpoints:**
- `GET /health` — health check
- `POST /v1/retrieve` — primary: `{query, top_k: 5, num_hops: 2}`
- Fallback: `POST /v1/query` if retrieve fails

**Response parsing:** Extracts `entities`, `relationships`, `passages` into formatted context string.

**Flow:** Graph context (no LLM tokens) → Gemini with structured knowledge graph prompt.

**Tuning for low accuracy:** Increase `num_hops` to 3, or `top_k` to 7.

**Prerequisites:**
1. Clone `https://github.com/tigergraph/graphrag`
2. `docker-compose up -d` OR TigerGraph Savanna
3. `python ingest_corpus.py`
4. `python scripts/verify_tigergraph.py`

---

## 9. Evaluation

### 9.1 BERTScore (`evaluation/bert_score_eval.py`)

- Model: `distilbert-base-uncased`
- Function: `compute_bertscore(predictions, references)` → `{precision, recall, f1, mean_f1, hashcode}`

### 9.2 LLM Judge (`evaluation/llm_judge.py`)

- Model: `meta-llama/Llama-3.1-8B-Instruct` via `huggingface_hub.InferenceClient`
- Requires: `HF_TOKEN` in `.env`
- Function: `judge_answer(question, ground_truth, generated_answer)` → `{verdict: PASS/FAIL/ERROR, reason, score: 0|1}`
- **Does NOT use Gemini** — preserves Gemini quota for pipelines

### 9.3 Benchmark Runner (`evaluation/run_benchmark.py`)

**Run:** `python evaluation/run_benchmark.py`

**Flow:**
1. Load 30 questions from `data/questions.json`
2. Init all 3 pipelines (P2 slow first time)
3. For each question: run P1, P2, P3 sequentially
4. **Save after each question** to `results/benchmark_results.json` (crash-safe resume)
5. Skip already-completed question IDs on re-run
6. Run BERTScore + LLM judge on all results
7. Print summary table
8. Generate `results/benchmark_report.md`

**Result record schema (per question):**
```json
{
  "question_id": 1,
  "category": "A",
  "question": "...",
  "ground_truth": "...",
  "pipeline1": {
    "pipeline": "LLM-Only",
    "answer": "...",
    "input_tokens": 45,
    "output_tokens": 120,
    "total_tokens": 165,
    "latency_seconds": 1.2,
    "context_tokens": 0,
    "bert_f1": 0.61,
    "llm_judge": "PASS",
    "llm_judge_reason": "..."
  },
  "pipeline2": { ... },
  "pipeline3": { ... }
}
```

**Pipeline keys:** `pipeline1`, `pipeline2`, `pipeline3`  
**Display names:** `LLM-Only`, `Basic-RAG`, `GraphRAG`

---

## 10. Utilities

### 10.1 Cost Calculator (`utils/cost_calculator.py`)

**Gemini 1.5 Flash pricing (for scale projections):**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

- `calculate_cost(input_tokens, output_tokens)` → USD float
- `calculate_monthly_cost_at_scale(avg_tokens, queries_per_day)` → `{daily_cost_usd, monthly_cost_usd}`

### 10.2 Token Counter (`utils/token_counter.py`)

- `count_tokens(text)` using tiktoken `cl100k_base`
- Used for corpus verification only

---

## 11. Dashboard (`dashboard/app.py`)

**Run:** `streamlit run dashboard/app.py` (from project root or dashboard dir)

**Tab 1 — Live Query:**
- Load all 3 pipelines (cached via `@st.cache_resource`)
- Category preset selector (A/B/C questions from `questions.json`)
- "Run All Pipelines" button → 3 columns with answers + metrics
- Token reduction callout (GraphRAG vs Basic RAG)
- Bar charts: token usage + cost per query

**Tab 2 — Full Benchmark Results:**
- Reads `results/benchmark_results.json` if exists
- Headline metrics: token reduction %, GraphRAG pass rate, avg BERTScore F1
- Per-category tables (A, B, C)

---

## 12. Scripts

### 12.1 Smoke Test (`tests/smoke_test.py`)

```bash
python tests/smoke_test.py
```

Tests one question ("What is the ACE2 receptor?") through P1 and P2 only. No TigerGraph required.

### 12.2 Verify TigerGraph (`scripts/verify_tigergraph.py`)

```bash
python scripts/verify_tigergraph.py
```

Checks: health → retrieve test → optional full P3 query.

### 12.3 Ingest Corpus (`ingest_corpus.py`)

```bash
python ingest_corpus.py
```

Ingests each doc from `corpus.json` into GraphRAG service. Tries endpoints: `/v1/documents`, `/ingest`, `/v1/ingest`. ~15–30 min for full corpus.

---

## 13. Execution Order (Step-by-Step)

```bash
cd graphrag-benchmark
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env: GEMINI_API_KEY, HF_TOKEN

python data/download_corpus.py          # Verify ≥2M tokens PASS
python tests/smoke_test.py              # P1 + P2 OK

# TigerGraph GraphRAG setup:
# git clone https://github.com/tigergraph/graphrag && docker-compose up -d
python scripts/verify_tigergraph.py
python ingest_corpus.py
python scripts/verify_tigergraph.py     # Confirm ingested

python evaluation/run_benchmark.py      # ~1 hour, 30 questions × 3 pipelines
# Fill BLOG_POST.md from results/benchmark_report.md
streamlit run dashboard/app.py          # Record demo video
```

---

## 14. Coding Rules (Enforce When Editing)

1. Every file starts with a module docstring
2. All API calls wrapped in try/except with clear errors
3. `tqdm` progress bars for loops >100 items
4. Never hardcode API keys — use `.env` + `python-dotenv`
5. Save benchmark results incrementally after each question
6. `time.sleep(1)` after every Gemini call
7. Pipeline token counts from `usage_metadata`, not tiktoken
8. Prefer simple, readable code over clever abstractions
9. No paid APIs (OpenAI, Anthropic, Pinecone, etc.)
10. No async/concurrent pipeline calls (sequential only)
11. No Docker for this repo's code (only TigerGraph GraphRAG repo uses Docker)
12. No authentication, no DB persistence beyond JSON files

---

## 15. What NOT to Build

- User authentication
- Database persistence (JSON files only)
- Docker for benchmark code itself
- Frontend frameworks other than Streamlit
- Model fine-tuning
- Paid API integrations

---

## 16. TigerGraph GraphRAG External Setup

**Repo:** https://github.com/tigergraph/graphrag

**Option A — Docker (local):**
```bash
git clone https://github.com/tigergraph/graphrag
cd graphrag && cp .env.example .env
# Add GEMINI_API_KEY
docker-compose up -d
curl http://localhost:8000/health
```

**Option B — Savanna (cloud):**
- Sign up at tgcloud.io ($60 free credits)
- Follow GraphRAG repo Savanna guide
- Set `TIGERGRAPH_GRAPHRAG_URL` to Savanna endpoint

Then from benchmark repo: `python ingest_corpus.py`

---

## 17. Demo Video Script (5–7 min)

1. **0:00–0:30** — Problem: complex LLM queries cost tokens; RAG retrieves too much
2. **0:30–1:00** — Dataset: CORD-19, 4000 papers, 2M+ tokens
3. **1:00–1:30** — Architecture: 3 pipelines, same LLM, different retrieval
4. **1:30–4:30** — Live dashboard:
   - Query 1 (Cat A): "What is the ACE2 receptor?" — all similar
   - Query 2 (Cat C): multi-hop protein/drug question — show token delta
5. **4:30–5:30** — Benchmark results tab, Category C pattern
6. **5:30–6:00** — Cost at 10K queries/day
7. **6:00–6:30** — GitHub link, wrap

---

## 18. Known Issues & Status

| Item | Status |
|------|--------|
| Project scaffold | ✅ Complete |
| Phase 2 updates (HF judge, smoke test, dashboard tabs) | ✅ Complete |
| `data/corpus.json` | ⚠️ Must be generated locally (`download_corpus.py`) — network-dependent |
| Full benchmark results | ⚠️ Run after corpus + API keys + GraphRAG service |
| `BLOG_POST.md` | 📝 Skeleton with `[X]` placeholders — fill after benchmark |

**Corpus download notes:**
- CSV from S3 may fail on flaky networks; script retries multiple URLs and caches to `data/metadata.csv`
- HuggingFace fallback: `allenai/cord19` if CSV fails
- Manual fallback: place `metadata.csv` in `data/` and re-run script

---

## 19. Dependencies (`requirements.txt`)

```
google-generativeai>=0.7.0
sentence-transformers>=3.0.0
chromadb>=0.5.0
streamlit>=1.35.0
tiktoken>=0.7.0
evaluate>=0.4.0
bert-score>=0.3.13
requests>=2.31.0
python-dotenv>=1.0.0
pandas>=2.0.0
tqdm>=4.66.0
pyTigerGraph>=1.6.0
huggingface_hub>=0.23.0
datasets>=2.19.0
```

---

## 20. Key File Responsibilities (Quick Reference)

| File | Responsibility |
|------|----------------|
| `pipelines/base.py` | Shared Gemini + token tracking |
| `pipelines/pipeline1_llm_only.py` | Baseline, no retrieval |
| `pipelines/pipeline2_basic_rag.py` | ChromaDB vector RAG |
| `pipelines/pipeline3_graphrag.py` | TigerGraph REST + Gemini |
| `evaluation/run_benchmark.py` | Full benchmark orchestration |
| `evaluation/llm_judge.py` | Llama PASS/FAIL judge |
| `evaluation/bert_score_eval.py` | BERTScore F1 |
| `data/download_corpus.py` | Build corpus.json |
| `data/questions.json` | 30 test questions |
| `dashboard/app.py` | Streamlit UI |
| `ingest_corpus.py` | Feed corpus to GraphRAG service |
| `scripts/verify_tigergraph.py` | Pre-flight GraphRAG checks |
| `tests/smoke_test.py` | Quick P1+P2 validation |
| `utils/cost_calculator.py` | USD cost math |
| `results/benchmark_results.json` | All run outputs |
| `results/benchmark_report.md` | Auto-generated report |
| `BLOG_POST.md` | Public-facing writeup |

---

## 21. Instructions for LLMs Working on This Project

When asked to modify this project:

1. **Read this file first** — it contains the full architectural context.
2. **Respect free-API rules** — never suggest paid alternatives.
3. **Preserve incremental saves** in `run_benchmark.py`.
4. **Keep Gemini for pipelines, Llama for judge** — do not swap back to Gemini judge.
5. **Test order:** smoke test (P1+P2) → verify TigerGraph → full benchmark.
6. **Token metrics matter** — hackathon judges verify `usage_metadata` counts.
7. **Category C is the story** — GraphRAG wins on multi-hop token reduction.
8. **Minimal diffs** — only change what's needed for the task.

---

*Last updated: Phase 2 complete. Project path: `graphrag-benchmark/` under TigerGraph hackathon workspace.*
