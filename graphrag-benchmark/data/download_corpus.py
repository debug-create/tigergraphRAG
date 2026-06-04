"""
download_corpus.py  —  Round 2 robust downloader.
Strategy : download the 5 parquet files directly (not streaming).
           Per-file retry + checkpoint means a network drop only retries
           the current file, never loses completed files.
"""

import os, json, time, io
from datetime import datetime
from dotenv import load_dotenv
import requests
import pyarrow.parquet as pq
from google import genai

load_dotenv()

TARGET_TOKENS     = 110_000_000
OUTPUT_PATH       = "data/corpus.json"
VERIFICATION_PATH = "data/token_count_verification.json"
PROGRESS_PATH     = "data/download_progress.json"
HF_API            = "https://datasets-server.huggingface.co/parquet?dataset=ccdv/pubmed-summarization"

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


# ── helpers ──────────────────────────────────────────────────────────────────

def get_parquet_urls() -> list[str]:
    print("Fetching parquet file list from HuggingFace datasets server...")
    r = requests.get(HF_API, timeout=30)
    r.raise_for_status()
    files = [
        f["url"]
        for f in r.json().get("parquet_files", [])
        if f.get("config") == "section" and f.get("split") == "train"
    ]
    if not files:
        raise RuntimeError("No parquet files found — HF API response:\n" + r.text[:500])
    print(f"  Found {len(files)} parquet file(s)")
    return files


def download_file(url: str, max_retries: int = 8) -> bytes:
    """Download a URL in 1 MB chunks with exponential back-off retry."""
    fname = url.split("/")[-1].split("?")[0]
    for attempt in range(max_retries):
        try:
            print(f"    Downloading {fname} (attempt {attempt + 1}/{max_retries})...")
            with requests.get(url, timeout=180, stream=True) as r:
                r.raise_for_status()
                chunks, total = [], 0
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    chunks.append(chunk)
                    total += len(chunk)
                    if total % (20 * 1024 * 1024) == 0:
                        print(f"      {total // (1024 * 1024)} MB so far...")
                print(f"    [OK] {fname}: {total // (1024*1024)} MB downloaded")
                return b"".join(chunks)
        except Exception as exc:
            if attempt < max_retries - 1:
                wait = min(60, 5 * (attempt + 1))
                print(f"    [FAIL] {exc}  - retrying in {wait}s")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Failed to download {fname} after {max_retries} attempts") from exc


def parquet_to_papers(data: bytes, file_tag: str) -> list[dict]:
    """Convert raw parquet bytes → list of corpus dicts."""
    table   = pq.read_table(io.BytesIO(data))
    columns = table.to_pydict()
    articles  = columns.get("article", [])
    abstracts = columns.get("abstract", [])

    papers = []
    for i, (article, abstract) in enumerate(zip(articles, abstracts)):
        article  = (article  or "").strip()
        abstract = (abstract or "").strip()
        if len(article) < 800:
            continue
        full_text = (
            f"Abstract:\n{abstract}\n\nFull Text:\n{article}"
            if abstract else article
        )
        papers.append({
            "text":     full_text,
            "title":    f"PubMed {file_tag}_{i}",
            "abstract": abstract,
            "metadata": {
                "paper_id": f"{file_tag}_{i}",
                "source":   "ccdv/pubmed-summarization",
            },
        })
    return papers


def load_checkpoint() -> tuple[list, set]:
    corpus, done = [], set()
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            corpus = json.load(f)
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            done = set(json.load(f).get("completed_files", []))
    if corpus or done:
        print(f"Resuming: {len(corpus):,} papers, {len(done)} file(s) already finished")
    return corpus, done


def save_checkpoint(corpus: list, done: set) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False)
    with open(PROGRESS_PATH, "w") as f:
        json.dump({"completed_files": list(done)}, f)


# ── token verification ────────────────────────────────────────────────────────

def verify_tokens(corpus: list[dict]) -> int:
    print("\nVerifying token count via Gemini count_tokens (sample + extrapolate)...")
    texts  = [p["text"] for p in corpus]
    sample = texts[:3000]
    chunk  = 100
    total  = 0

    for i in range(0, len(sample), chunk):
        combined = "\n\n---PAPER---\n\n".join(sample[i : i + chunk])
        resp = client.models.count_tokens(
            model="gemini-2.5-flash",
            contents=combined,
        )
        total += resp.total_tokens
        time.sleep(1)
        if (i // chunk + 1) % 5 == 0:
            print(f"  {i // chunk + 1} chunks done | running: {total / 1_000_000:.1f}M")

    if len(texts) > len(sample):
        total = int(total * len(texts) / len(sample))
        print(f"  Extrapolated to full {len(texts):,} papers -> {total / 1_000_000:.1f}M tokens")

    return total


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs("data", exist_ok=True)

    urls           = get_parquet_urls()
    corpus, done   = load_checkpoint()
    total_chars    = sum(len(p["text"]) for p in corpus)

    for idx, url in enumerate(urls):
        fname = url.split("/")[-1].split("?")[0]

        if fname in done:
            print(f"File {idx + 1}/{len(urls)}: {fname} — already complete, skipping")
            continue

        est = total_chars // 4
        if est >= int(TARGET_TOKENS * 1.15):
            print(f"Target reached (~{est / 1_000_000:.1f}M est tokens). No more files needed.")
            break

        print(f"\nFile {idx + 1}/{len(urls)}: {fname}")
        raw    = download_file(url)
        papers = parquet_to_papers(raw, f"f{idx}")

        corpus.extend(papers)
        total_chars += sum(len(p["text"]) for p in papers)
        done.add(fname)
        save_checkpoint(corpus, done)

        print(
            f"  +{len(papers):,} papers | total: {len(corpus):,} "
            f"| ~{total_chars // 4 / 1_000_000:.1f}M tokens (est)"
        )

    # ── final verification ──
    total_tokens = verify_tokens(corpus)

    verification = {
        "total_tokens":         total_tokens,
        "paper_count":          len(corpus),
        "avg_tokens_per_paper": total_tokens // max(len(corpus), 1),
        "verified_with":        "google-genai  gemini-2.5-flash  count_tokens",
        "timestamp":            datetime.utcnow().isoformat() + "Z",
        "target_was":           TARGET_TOKENS,
        "target_met":           total_tokens >= TARGET_TOKENS,
        "files_used":           list(done),
    }
    with open(VERIFICATION_PATH, "w") as f:
        json.dump(verification, f, indent=2)

    print(f"\n{'=' * 55}")
    print(f"Papers saved     : {len(corpus):,}")
    print(f"Total tokens     : {total_tokens / 1_000_000:.1f}M")
    print(f"Avg tokens/paper : {total_tokens // max(len(corpus), 1):,}")
    print(f"Target met       : {'YES [OK]' if total_tokens >= TARGET_TOKENS else 'NO - run again'}")
    print(f"Files completed  : {len(done)}/{len(urls)}")


if __name__ == "__main__":
    main()
