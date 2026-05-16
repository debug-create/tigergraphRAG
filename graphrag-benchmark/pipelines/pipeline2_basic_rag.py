"""Pipeline 2: Basic RAG with sentence-transformers + ChromaDB."""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from pipelines.base import BasePipeline


class BasicRAGPipeline(BasePipeline):
    """Vector retrieval over chunked CORD-19 abstracts, then Gemini generation."""

    def __init__(self, corpus_path: str = "data/corpus.json", top_k: int = 5):
        """
        Load embedder, index corpus into persistent ChromaDB (skips re-embedding if index exists).

        Args:
            corpus_path: Path to corpus.json.
            top_k: Number of chunks to retrieve per query.
        """
        super().__init__("Basic-RAG")
        self.top_k = top_k

        print("Loading embedding model...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        import hashlib  # noqa: F401 – available for future collection versioning
        persist_dir = "data/chroma_index"
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)

        # get_or_create_collection is atomic: loads existing index or creates fresh one.
        # We check count() to decide whether to re-index.
        self.collection = self.chroma_client.get_or_create_collection(
            name="cord19",
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() > 0:
            print("[OK] Loaded existing ChromaDB index from disk (skipping re-embedding)")
        else:
            print("Building ChromaDB index for first time (one-time ~15 min)...")
            self._index_corpus(corpus_path)


    def _chunk_text(self, text: str, chunk_size: int = 256, overlap: int = 32) -> list[str]:
        """
        Split text into overlapping word-based chunks.

        Args:
            text: Full document text.
            chunk_size: Target words per chunk.
            overlap: Words repeated between adjacent chunks.

        Returns:
            List of chunk strings.
        """
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            start += chunk_size - overlap
        return chunks

    def _index_corpus(self, corpus_path: str):
        """
        Load corpus, chunk abstracts, embed, and store in ChromaDB.

        Args:
            corpus_path: Path to corpus.json.
        """
        path = Path(corpus_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"Corpus not found: {corpus_path}. Run: python data/download_corpus.py"
            )
        with open(path, encoding="utf-8") as f:
            corpus = json.load(f)
        if not corpus:
            raise ValueError("corpus.json is empty.")

        all_chunks = []
        all_ids = []
        all_metadata = []

        for doc in corpus:
            text = f"{doc['title']}. {doc['abstract']}"
            chunks = self._chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{doc['id']}_chunk_{i}")
                all_metadata.append({
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "chunk_index": i,
                })

        print(f"Embedding {len(all_chunks)} chunks...")
        batch_size = 256
        for i in tqdm(range(0, len(all_chunks), batch_size)):
            batch_texts = all_chunks[i : i + batch_size]
            batch_ids = all_ids[i : i + batch_size]
            batch_meta = all_metadata[i : i + batch_size]
            embeddings = self.embedder.encode(batch_texts).tolist()
            self.collection.add(
                documents=batch_texts,
                embeddings=embeddings,
                ids=batch_ids,
                metadatas=batch_meta,
            )
        print(f"Indexed {len(all_chunks)} chunks into ChromaDB.")

    def retrieve(self, question: str) -> list[str]:
        """
        Embed question and retrieve top_k similar chunks.

        Args:
            question: Query string.

        Returns:
            List of retrieved chunk texts.
        """
        q_embedding = self.embedder.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=q_embedding,
            n_results=self.top_k,
        )
        return results["documents"][0]

    def query(self, question: str) -> dict:
        """
        Retrieve context chunks and generate answer with Gemini.

        Args:
            question: User question.

        Returns:
            Result dict with answer, tokens, and retrieved context.
        """
        chunks = self.retrieve(question)
        if not chunks:
            chunks = ["No relevant context found in the corpus."]
        context = "\n\n---\n\n".join(chunks)

        prompt = f"""You are a biomedical research assistant. Answer the question using ONLY the provided context.
If the context does not contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""

        result = self.call_llm(prompt)
        result["pipeline"] = self.name
        result["context_used"] = context
        result["context_tokens"] = result["input_tokens"]
        return result
