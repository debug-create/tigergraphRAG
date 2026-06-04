<p align="center">
  <h1 align="center">🐯 MediGraph — GraphRAG Inference Benchmark</h1>
  <p align="center">
    <strong>Proving GraphRAG beats RAG on token efficiency at biomedical scale</strong>
  </p>
  <p align="center">
    <a href="https://tiger-graph-rag-topaz.vercel.app/">🌐 Live Dashboard</a> · 
    <a href="#results">📊 Results</a> · 
    <a href="#quickstart">🚀 Quickstart</a> · 
    <a href="graphrag-benchmark/BLOG_POST.md">📝 Blog Post</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/TigerGraph-GraphRAG_Hackathon_2026-orange?style=for-the-badge" alt="Hackathon Badge"/>
    <img src="https://img.shields.io/badge/LLM-Gemini_2.5_Flash-blue?style=for-the-badge" alt="LLM Badge"/>
    <img src="https://img.shields.io/badge/Cost-$0_Total-green?style=for-the-badge" alt="Cost Badge"/>
    <img src="https://img.shields.io/badge/Corpus-CORD--19_2M+_Tokens-purple?style=for-the-badge" alt="Corpus Badge"/>
  </p>
</p>

---

## 💡 What is this?

MediGraph is a **head-to-head benchmark** that runs the **same 30 biomedical questions** through three inference pipelines — all using the same LLM — to prove that **GraphRAG delivers more accurate answers with fewer tokens** compared to traditional RAG.

| Pipeline | Retrieval Method | What Gets Sent to the LLM |
|----------|-----------------|---------------------------|
| **LLM-Only** | None | Just the question |
| **Basic RAG** | ChromaDB vector similarity → top-5 chunks | Similar paragraphs (broad) |
| **GraphRAG** | TigerGraph multi-hop traversal | Focused knowledge subgraph (precise) |

> **Core insight:** Basic RAG retrieves *similar* text. GraphRAG retrieves *connected facts*. For multi-hop questions, that means fewer tokens and better answers.

---

<a id="results"></a>
## 📊 Benchmark Results

**30 questions × 3 pipelines** on the CORD-19 biomedical corpus (~6,000 papers, 2M+ tokens).

### Headline Metrics

| Pipeline | Avg Tokens | Pass Rate | BERTScore F1 | Cost/Query |
|---|---|---|---|---|
| LLM-Only | 282 | 90.0% | 0.727 | $0.000017 |
| Basic RAG | 963 | 90.0% | 0.710 | $0.000059 |
| **GraphRAG** | **874** | **100.0%** | **0.785** | **$0.000052** |

### Token Reduction by Question Complexity

| Category | Type | Token Δ vs RAG | GraphRAG Pass Rate |
|---|---|---|---|
| **A** — Single-hop | Factual lookup | −4.8% | 100% |
| **B** — Two-hop | Relational | −33.5% | 90% |
| **C** — Three-hop | Multi-hop complex | Best on BERTScore | 60% |

> **Category B is the sweet spot** — GraphRAG's graph traversal returns a focused subgraph instead of broad vector matches, cutting tokens by a third while maintaining accuracy.

### Evaluation Stack

| Metric | Tool | Model |
|--------|------|-------|
| Token Count | `usage_metadata` | Gemini response API |
| BERTScore F1 | `evaluate` + `bert-score` | `distilbert-base-uncased` (local) |
| LLM-as-Judge | HuggingFace Inference | `Llama-3.1-8B-Instruct` |
| Cost | Gemini 1.5 Flash pricing | $0.075/1M in, $0.30/1M out |

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────┐
                    │         Same 30 Questions                │
                    │       (data/questions.json)              │
                    └────────────────────┬────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│   Pipeline 1    │           │   Pipeline 2    │           │   Pipeline 3    │
│   LLM-Only      │           │   Basic RAG     │           │   GraphRAG      │
│                 │           │                 │           │                 │
│  Question       │           │  Embed query    │           │  TigerGraph     │
│     ↓           │           │     ↓           │           │  multi-hop      │
│  Gemini Flash   │           │  ChromaDB       │           │  traversal      │
│  (no context)   │           │  top-5 chunks   │           │     ↓           │
│                 │           │     ↓           │           │  Structured     │
│                 │           │  Gemini Flash   │           │  subgraph       │
│                 │           │  (+ chunks)     │           │     ↓           │
│                 │           │                 │           │  Gemini Flash   │
└────────┬────────┘           └────────┬────────┘           └────────┬────────┘
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │     BERTScore + LLM Judge + Report       │
                    └─────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Gemini 2.5 Flash | Free tier |
| Graph DB | TigerGraph + [GraphRAG](https://github.com/tigergraph/graphrag) | Free (Docker) |
| Vector Store | ChromaDB (in-memory) | Free (local) |
| Embeddings | `all-MiniLM-L6-v2` | Free (local) |
| LLM Judge | Llama-3.1-8B via HuggingFace | Free tier |
| BERTScore | `distilbert-base-uncased` | Free (local) |
| Dashboard | Next.js 16 + Tailwind | Vercel free |
| **Total cost** | | **$0** |

---

<a id="quickstart"></a>
## 🚀 Quickstart

### Prerequisites

- Python 3.10+, Node.js 18+, Docker
- [Google AI Studio API key](https://aistudio.google.com/) (free)
- [HuggingFace token](https://huggingface.co/settings/tokens) (free)

### 1. Clone & Setup

```bash
git clone https://github.com/debug-create/tigergraphRAG.git
cd tigergraphRAG

# Python backend
cd graphrag-benchmark
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate          # macOS/Linux
pip install -r requirements.txt

cp .env.example .env
# Edit .env → add GEMINI_API_KEY, HF_TOKEN
```

### 2. Start TigerGraph GraphRAG (Docker)

```bash
cd graphrag
cp .env.example .env
# Add GEMINI_API_KEY to configs/server_config.json
docker compose up -d
```

### 3. Ingest Corpus & Verify

```bash
cd graphrag-benchmark
python data/download_corpus.py          # Download CORD-19 corpus
python tests/smoke_test.py              # Verify P1 + P2
python scripts/verify_tigergraph.py     # Verify GraphRAG service
python ingest_corpus.py                 # Ingest into TigerGraph
```

### 4. Run Full Benchmark

```bash
python evaluation/run_benchmark.py      # 30 questions × 3 pipelines
```

### 5. Launch Dashboard

```bash
# Terminal 1 — API server
cd graphrag-benchmark
.venv\Scripts\activate
uvicorn api_server:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 — Next.js dashboard
cd medi-graph-dashboard
npm install && npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 📁 Project Structure

```
tigergraphRAG/
├── graphrag-benchmark/          # Benchmark engine
│   ├── pipelines/               # 3 inference pipelines
│   │   ├── pipeline1_llm_only.py
│   │   ├── pipeline2_basic_rag.py
│   │   └── pipeline3_graphrag.py
│   ├── evaluation/              # BERTScore + LLM Judge
│   ├── data/                    # CORD-19 corpus + 30 questions
│   ├── results/                 # benchmark_results.json + report
│   ├── api_server.py            # FastAPI bridge for dashboard
│   ├── dashboard/               # Streamlit alternative
│   └── BLOG_POST.md             # Hackathon blog post
│
├── medi-graph-dashboard/        # Next.js 16 dashboard (deployed)
│   ├── app/                     # App router pages
│   ├── components/              # UI components
│   └── lib/api.ts               # API client
│
└── graphrag/                    # TigerGraph GraphRAG (submodule)
    ├── docker-compose.yml
    └── configs/
```

---

## 🌐 Live Demo

**[tiger-graph-rag-topaz.vercel.app](https://tiger-graph-rag-topaz.vercel.app/)**

The deployed dashboard showcases benchmark results with interactive cost projections and a live query interface. When connected to the local API server, it runs real-time pipeline comparisons.

---

## 📝 Blog Post

Read the full writeup: **[BLOG_POST.md](graphrag-benchmark/BLOG_POST.md)**

---

## 🏆 Hackathon Submission

Built for the **TigerGraph GraphRAG Inference Hackathon 2026**.

**#GraphRAGInferenceHackathon @TigerGraph**

---

## 📄 License

Hackathon submission — see individual components for their licenses.
