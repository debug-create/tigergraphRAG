"""
Download and process the CORD-19 metadata CSV into corpus.json.
Targets ~2M tokens (cl100k_base) from filtered abstracts.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import tiktoken
from tqdm import tqdm

# Allow imports from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.token_counter import count_tokens

METADATA_URLS = [
    "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/metadata.csv",
    "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2023-06-26/metadata.csv",
    "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2022-06-02/metadata.csv",
]
OUTPUT_PATH = Path(__file__).resolve().parent / "corpus.json"
CACHE_CSV = Path(__file__).resolve().parent / "metadata.csv"
MIN_TOKENS = 2_000_000
INITIAL_ROWS = 5000
CSV_COLUMNS = ["cord_uid", "title", "abstract", "authors", "journal", "publish_time"]


def _read_metadata_partial(path: Path, max_bytes: int = 95_000_000) -> pd.DataFrame:
    """Read the start of a large CSV up to the last complete line (avoids EOF-in-string errors)."""
    from io import StringIO

    with open(path, "rb") as f:
        raw = f.read(max_bytes)
    text = raw.decode("utf-8", errors="replace")
    last_nl = text.rfind("\n")
    if last_nl > 0:
        text = text[:last_nl]
    df = pd.read_csv(
        StringIO(text),
        on_bad_lines="skip",
        engine="python",
        dtype=str,
        usecols=CSV_COLUMNS,
    )
    print(f"Partial read: {len(df)} rows from first {max_bytes // 1_000_000}MB of file.")
    return df


def read_metadata_csv(path: Path = CACHE_CSV) -> pd.DataFrame:
    """
    Read metadata CSV, skipping malformed rows (broken quotes around row ~48k / ~107k).

    Tries chunked read first; on failure keeps valid chunks or falls back to partial file read.

    Args:
        path: Path to metadata.csv.

    Returns:
        DataFrame with standard CORD-19 metadata columns.
    """
    print(f"Reading CSV in chunks (skipping bad lines): {path}")
    chunks = []
    reader = pd.read_csv(
        path,
        chunksize=20000,
        on_bad_lines="skip",
        engine="python",
        dtype=str,
        usecols=CSV_COLUMNS,
    )
    while True:
        try:
            chunks.append(next(reader))
        except StopIteration:
            break
        except Exception as e:
            print(f"  Chunk read stopped after {len(chunks)} chunks: {e}")
            break

    if chunks:
        df = pd.concat(chunks, ignore_index=True)
        print(f"Loaded {len(df)} rows from chunked read.")
        return df

    return _read_metadata_partial(path)


def download_csv_with_retries(url: str, dest: Path, max_retries: int = 5) -> bool:
    """
    Download CSV to disk with retries (more reliable than pd.read_csv on flaky networks).

    Returns:
        True if download succeeded.
    """
    session = requests.Session()
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}: {url}")
            with session.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            print(f"  Download failed: {e}")
            time.sleep(2 ** attempt)
    return False


def download_metadata_csv() -> pd.DataFrame:
    """Try multiple CORD-19 CSV URLs; use cached file if present."""
    if CACHE_CSV.exists() and CACHE_CSV.stat().st_size > 1_000_000:
        print(f"Using cached CSV: {CACHE_CSV}")
        return read_metadata_csv(CACHE_CSV)

    for url in METADATA_URLS:
        print(f"Downloading CORD-19 metadata from {url}...")
        if download_csv_with_retries(url, CACHE_CSV):
            df = read_metadata_csv(CACHE_CSV)
            print(f"Downloaded {len(df)} rows (after skipping bad lines).")
            return df

    raise RuntimeError("All CSV download URLs failed.")


def download_metadata_hf_fallback() -> pd.DataFrame:
    """
    Fallback: load CORD-19 via HuggingFace datasets when CSV download fails.

    Returns:
        DataFrame with cord_uid, title, abstract, authors, publish_time, journal.
    """
    print("Using HuggingFace datasets fallback for CORD-19...")
    from datasets import load_dataset

    configs = ["metadata", "default"]
    last_error = None
    for config in configs:
        try:
            kwargs = {"path": "allenai/cord19", "split": "train"}
            if config != "default":
                kwargs["name"] = config
            dataset = load_dataset(**kwargs)
            df = dataset.to_pandas()
            if "cord_uid" not in df.columns and "sha" in df.columns:
                df = df.rename(columns={"sha": "cord_uid"})
            print(f"Loaded {len(df)} rows from HuggingFace (config={config}).")
            return df
        except Exception as e:
            last_error = e
            print(f"  HF config '{config}' failed: {e}")
    raise RuntimeError(f"HuggingFace fallback failed: {last_error}")


def download_metadata() -> pd.DataFrame:
    """
    Download CORD-19 metadata CSV with retries, then HF fallback.

    Returns:
        Raw metadata DataFrame.
    """
    try:
        return download_metadata_csv()
    except Exception as e:
        print(f"CSV download failed: {e}")
        return download_metadata_hf_fallback()


def filter_and_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep required columns and filter rows with valid abstracts.

    Args:
        df: Raw metadata DataFrame.

    Returns:
        Filtered DataFrame sorted by publish_time descending.
    """
    columns = ["cord_uid", "title", "abstract", "authors", "publish_time", "journal"]
    available = [c for c in columns if c in df.columns]
    df = df[available].copy()

    df = df[df["abstract"].notna()]
    df["abstract"] = df["abstract"].astype(str)
    df = df[df["abstract"].str.len() > 100]

    if "cord_uid" not in df.columns:
        raise ValueError("metadata must include cord_uid column")

    if "publish_time" in df.columns:
        df = df.sort_values("publish_time", ascending=False)

    return df.reset_index(drop=True)


def build_corpus_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert DataFrame rows to corpus JSON records.

    Args:
        df: Filtered metadata DataFrame.

    Returns:
        List of document dicts.
    """
    records = []
    for _, row in df.iterrows():
        authors = row.get("authors", "")
        if pd.isna(authors):
            authors = ""
        publish = row.get("publish_time", "")
        if pd.isna(publish):
            publish = ""
        journal = row.get("journal", "")
        if pd.isna(journal):
            journal = ""

        records.append({
            "id": str(row["cord_uid"]),
            "title": str(row.get("title", "") or ""),
            "abstract": str(row["abstract"]),
            "authors": str(authors),
            "journal": str(journal),
            "publish_time": str(publish),
        })
    return records


def count_corpus_tokens(records: list[dict]) -> int:
    """
    Count total tokens across title + abstract for all records.

    Args:
        records: Corpus document list.

    Returns:
        Total token count using cl100k_base.
    """
    total = 0
    for doc in tqdm(records, desc="Counting tokens"):
        text = f"{doc['title']}. {doc['abstract']}"
        total += count_tokens(text)
    return total


def verify_corpus(corpus_path: Path = OUTPUT_PATH) -> bool:
    """
    Verify saved corpus meets >= 2M token requirement.

    Returns:
        True if token count passes threshold.
    """
    with open(corpus_path, encoding="utf-8") as f:
        corpus = json.load(f)

    enc = tiktoken.get_encoding("cl100k_base")
    total_tokens = sum(
        len(enc.encode(f"{doc['title']}. {doc['abstract']}"))
        for doc in corpus
    )
    print(f"Docs: {len(corpus)}")
    print(f"Total tokens: {total_tokens:,}")
    passed = total_tokens >= MIN_TOKENS
    print(f"Status: {'PASS' if passed else 'NEED MORE ROWS'}")
    if not passed:
        print("Increase the row limit in download_corpus.py and re-run.")
    return passed


def build_from_cache_only() -> pd.DataFrame:
    """Load corpus from cached metadata.csv only (no network)."""
    if not CACHE_CSV.exists():
        raise FileNotFoundError(f"Missing {CACHE_CSV}. Download metadata first or run without --cache-only.")
    return read_metadata_csv(CACHE_CSV)


def main():
    """Download, filter, verify token count, and save corpus.json."""
    import argparse

    parser = argparse.ArgumentParser(description="Build CORD-19 corpus.json")
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Use data/metadata.csv only (skip download)",
    )
    args = parser.parse_args()

    try:
        if args.cache_only:
            df = build_from_cache_only()
        else:
            df = download_metadata()
    except Exception as e:
        print(f"\nCould not load corpus: {e}")
        print("Retry when online, or run: python data/download_corpus.py --cache-only")
        sys.exit(1)

    df = filter_and_prepare(df)
    print(f"After filtering: {len(df)} documents with valid abstracts.")

    n_rows = INITIAL_ROWS
    while n_rows <= len(df):
        subset = df.head(n_rows)
        records = build_corpus_records(subset)
        total_tokens = count_corpus_tokens(records)
        print(f"Rows={n_rows} -> {len(records)} docs, {total_tokens:,} tokens")

        if total_tokens >= MIN_TOKENS:
            break
        n_rows = min(n_rows + 1000, len(df))
        print(f"Under {MIN_TOKENS:,} tokens, expanding to {n_rows} rows...")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    avg_abstract = sum(len(d["abstract"]) for d in records) / len(records)
    print("\n=== Corpus Summary ===")
    print(f"Total documents: {len(records)}")
    print(f"Total tokens (cl100k_base): {total_tokens:,}")
    print(f"Average abstract length (chars): {avg_abstract:.0f}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("\n=== Verification ===")
    verify_corpus(OUTPUT_PATH)


if __name__ == "__main__":
    main()
