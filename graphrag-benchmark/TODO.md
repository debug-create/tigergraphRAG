# Submission Checklist

## You must run locally (requires API keys + network)

- [ ] `copy .env.example .env` and set `GEMINI_API_KEY`, `HF_TOKEN`
- [ ] `pip install -r requirements.txt`
- [ ] `python scripts/check_setup.py`
- [ ] `python data/download_corpus.py` → verify **≥2M tokens PASS**
- [ ] `python tests/smoke_test.py`
- [ ] TigerGraph GraphRAG: `docker-compose up -d` in [tigergraph/graphrag](https://github.com/tigergraph/graphrag)
- [ ] `python scripts/verify_tigergraph.py`
- [ ] `python ingest_corpus.py` (15–30 min; resumes via `data/ingest_checkpoint.json`)
- [ ] `python evaluation/run_benchmark.py` (~1 hour)
- [ ] `python scripts/fill_blog_post.py`
- [ ] `streamlit run dashboard/app.py` → record demo
- [ ] Push to GitHub and submit

## If GraphRAG pass rate < 90%

Tune `num_hops` / `top_k` in `pipelines/pipeline3_graphrag.py` and re-run failed questions only.

## If corpus download fails

1. Retry when online, or  
2. Manually download CORD-19 `metadata.csv` into `data/metadata.csv` and re-run `download_corpus.py`
