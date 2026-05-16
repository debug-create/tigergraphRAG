"""
Streamlit comparison dashboard for LLM-Only vs Basic RAG vs GraphRAG.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.cost_calculator import calculate_cost

st.set_page_config(
    page_title="GraphRAG Inference Benchmark",
    layout="wide",
    page_icon="🐯",
)

st.title("🐯 GraphRAG Inference Benchmark")
st.caption("LLM-Only vs Basic RAG vs GraphRAG — head-to-head on CORD-19 biomedical corpus")

corpus_path = ROOT / "data" / "corpus.json"
results_path = ROOT / "results" / "benchmark_results.json"
if not corpus_path.exists():
    st.warning("`data/corpus.json` not found. Run `python data/download_corpus.py` first.")

tab1, tab2 = st.tabs(["🔴 Live Query", "📊 Full Benchmark Results"])


@st.cache_resource
def load_pipelines():
    """Load all three pipelines (cached; first load embeds corpus ~5 min)."""
    from pipelines.pipeline1_llm_only import LLMOnlyPipeline
    from pipelines.pipeline2_basic_rag import BasicRAGPipeline
    from pipelines.pipeline3_graphrag import GraphRAGPipeline

    return (
        LLMOnlyPipeline(),
        BasicRAGPipeline(corpus_path=str(corpus_path)),
        GraphRAGPipeline(),
    )


def run_pipeline(name, pipeline, question):
    """Execute pipeline and return result dict."""
    try:
        return pipeline.query(question)
    except Exception as e:
        return {
            "answer": str(e),
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_seconds": 0,
        }


with tab1:
    questions_path = ROOT / "data" / "questions.json"
    with open(questions_path, encoding="utf-8") as f:
        all_questions = json.load(f)

    col_input, col_preset = st.columns([2, 1])
    with col_preset:
        category = st.selectbox(
            "Preset category",
            ["Custom", "A - Single hop", "B - Two hop", "C - Three hop"],
        )
        preset_q = ""
        if category != "Custom":
            cat_letter = category[0]
            cat_qs = [q for q in all_questions if q["category"] == cat_letter]
            preset_q = st.selectbox("Question", [q["question"] for q in cat_qs])

    with col_input:
        question = st.text_area("Your question", value=preset_q, height=100)

    if st.button("Load pipelines", help="First load embeds corpus (~5 min)"):
        with st.spinner("Loading pipelines (this may take several minutes)..."):
            st.session_state["pipelines"] = load_pipelines()
        st.success("Pipelines loaded and cached.")

    run_btn = st.button("🚀 Run All Pipelines", type="primary", use_container_width=True)

    if run_btn:
        if not question.strip():
            st.warning("Enter a question first.")
        elif "pipelines" not in st.session_state:
            st.error("Click **Load pipelines** before running queries.")
        else:
            p1, p2, p3 = st.session_state["pipelines"]
            configs = [
                ("LLM-Only", p1, "🔴"),
                ("Basic RAG", p2, "🟡"),
                ("GraphRAG", p3, "🟢"),
            ]
            results = {}
            cols = st.columns(3)
            for col, (name, pipe, icon) in zip(cols, configs):
                with col:
                    st.subheader(f"{icon} {name}")
                    with st.spinner(f"Running {name}..."):
                        result = run_pipeline(name, pipe, question)
                    results[name] = result
                    st.text_area("Answer", result["answer"], height=280, key=f"ans_{name}")
                    cost = calculate_cost(result["input_tokens"], result["output_tokens"])
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Tokens", result["total_tokens"])
                    m2.metric("Latency", f"{result['latency_seconds']}s")
                    m3.metric("Cost", f"${cost:.6f}")
                    # LLM Judge verdict (shown after evaluation run)
                    verdict = result.get("llm_judge", None)
                    if verdict == "PASS":
                        st.success("✅ Judge: PASS")
                    elif verdict == "FAIL":
                        st.error("❌ Judge: FAIL")
                    elif result.get("error"):
                        st.warning(f"⚠️ {result['error']}")

            st.subheader("📊 Comparison")
            summary = pd.DataFrame([
                {
                    "Pipeline": n,
                    "Tokens": r["total_tokens"],
                    "Latency (s)": r["latency_seconds"],
                    "Cost ($)": calculate_cost(r["input_tokens"], r["output_tokens"]),
                }
                for n, r in results.items()
            ])
            st.dataframe(summary, use_container_width=True, hide_index=True)

            bt, gt = results["Basic RAG"]["total_tokens"], results["GraphRAG"]["total_tokens"]
            if bt > 0:
                red = (bt - gt) / bt * 100
                st.success(f"GraphRAG used **{red:.1f}%** fewer tokens than Basic RAG") if red > 0 else st.warning(
                    f"GraphRAG used **{abs(red):.1f}%** more tokens than Basic RAG"
                )

            chart = summary.set_index("Pipeline")
            cc1, cc2 = st.columns(2)
            cc1.subheader("Tokens")
            cc1.bar_chart(chart["Tokens"])
            cc2.subheader("Cost (USD)")
            cc2.bar_chart(chart["Cost ($)"])

with tab2:
    st.subheader("30-Question Benchmark Results")
    if not results_path.exists():
        st.info("No results yet. Run: `python evaluation/run_benchmark.py`")
    else:
        with open(results_path, encoding="utf-8") as f:
            all_results = json.load(f)

        rows = []
        for r in all_results:
            for p_key in ("pipeline1", "pipeline2", "pipeline3"):
                if p_key not in r:
                    continue
                p = r[p_key]
                rows.append({
                    "Q#": r["question_id"],
                    "Cat": r["category"],
                    "Pipeline": p["pipeline"],
                    "Tokens": p["total_tokens"],
                    "Latency": p["latency_seconds"],
                    "Cost ($)": p.get(
                        "cost_usd",
                        calculate_cost(p["input_tokens"], p["output_tokens"]),
                    ),
                    "Judge": p.get("llm_judge", "—"),
                    "BERT F1": round(p.get("bert_f1", 0), 3),
                })
        df = pd.DataFrame(rows)

        if df.empty:
            st.warning("Results file is empty.")
        else:
            g = df[df["Pipeline"] == "GraphRAG"]
            b = df[df["Pipeline"] == "Basic-RAG"]
            if not g.empty and not b.empty:
                red = (b["Tokens"].mean() - g["Tokens"].mean()) / b["Tokens"].mean() * 100
                pr = (g["Judge"] == "PASS").mean() * 100
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Token reduction vs RAG", f"{red:.1f}%")
                c2.metric("GraphRAG pass rate", f"{pr:.1f}%")
                c3.metric("Avg BERT F1 (GraphRAG)", f"{g['BERT F1'].mean():.3f}")
                c4.metric("Questions done", len(all_results))

            st.subheader("Headline comparison")
            headline = df.groupby("Pipeline").agg(
                Tokens=("Tokens", "mean"),
                Latency=("Latency", "mean"),
                Cost=("Cost ($)", "mean"),
                PassRate=("Judge", lambda s: (s == "PASS").mean() * 100),
                BERT=("BERT F1", "mean"),
            ).round(3)
            st.dataframe(headline, use_container_width=True)

            st.subheader("By category")
            for cat, label in [("A", "Single-hop"), ("B", "Two-hop"), ("C", "Three-hop")]:
                st.markdown(f"**Category {cat} — {label}**")
                st.dataframe(df[df["Cat"] == cat], use_container_width=True, hide_index=True)

            st.subheader("Avg tokens by pipeline")
            st.bar_chart(df.groupby("Pipeline")["Tokens"].mean())
