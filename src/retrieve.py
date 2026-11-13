# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Retrieve: find the documentation passages that bear on a ticket.

Acceptance criteria A4 (passages resolve to the real corpus) and the Build
Spec rule "return nothing rather than something irrelevant".
"""
import json
import re
from pathlib import Path

import numpy as np

from src.models import Passage


# --------------------------------------------------------------------------
# Chunking (a design DECISION, compared in evaluation/tune.py)
# --------------------------------------------------------------------------
def chunk_document(doc: dict, strategy: str) -> list:
    """Split one article into passages.

    "whole":   the full article is one passage (articles are short, ~1,100 chars).
    "section": one passage per ## section, each prefixed with the article title
               so it still makes sense on its own. The numbered Resolution steps
               stay together in one passage, never split mid-sequence.
    """
    title = doc.get("title", "")
    content = doc.get("content", "")
    if strategy == "whole":
        return [{"text": content, "section": "all"}]

    parts = re.split(r"\n(?=## )", content)
    chunks = []
    for part in parts:
        heading = part.splitlines()[0].lstrip("#").strip() if part.strip() else ""
        if not part.strip() or part.lstrip().startswith("# "):
            # the top "# Title / Applies to" block: fold into the title prefix
            continue
        chunks.append({"text": f"{title}\n{part.strip()}", "section": heading})
    return chunks or [{"text": content, "section": "all"}]


def build_passages(docs_path: Path, strategy: str) -> list:
    docs = json.loads(Path(docs_path).read_text(encoding="utf-8"))
    passages = []
    for doc in docs:
        for i, chunk in enumerate(chunk_document(doc, strategy)):
            passages.append({
                "passage_id": f"{doc['doc_id']}#{i}",
                "doc_id": doc["doc_id"],
                "title": doc.get("title", ""),
                "section": chunk["section"],
                "text": chunk["text"],
            })
    return passages


# --------------------------------------------------------------------------
# Vector indexes (swappable): Chroma on disk, or a simple in-memory numpy index
# --------------------------------------------------------------------------
class MemoryIndex:
    def __init__(self, passages, vectors):
        self.passages = passages
        self.vectors = vectors

    def search(self, query_vec, k):
        scores = self.vectors @ query_vec                        # cosine similarity
        order = np.argsort(-scores)[:k]
        return [(self.passages[i], float(scores[i])) for i in order]


class ChromaIndex:
    def __init__(self, passages, vectors, path: Path, collection_name: str):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        client = chromadb.PersistentClient(path=str(path),
                                           settings=ChromaSettings(anonymized_telemetry=False))
        self.collection = client.get_or_create_collection(collection_name)
        if self.collection.count() != len(passages):             # rebuild if corpus changed
            client.delete_collection(collection_name)
            self.collection = client.get_or_create_collection(collection_name)
            self.collection.add(
                ids=[p["passage_id"] for p in passages],
                embeddings=vectors.tolist(),
                documents=[p["text"] for p in passages],
                metadatas=[{"doc_id": p["doc_id"], "title": p["title"], "section": p["section"]}
                           for p in passages],
            )
        self.by_id = {p["passage_id"]: p for p in passages}

    def search(self, query_vec, k):
        res = self.collection.query(query_embeddings=[query_vec.tolist()], n_results=k)
        out = []
        for pid, dist in zip(res["ids"][0], res["distances"][0]):
            # Chroma's default distance is squared L2. For unit vectors:
            # squared_L2 = 2 - 2*cosine  ->  cosine = 1 - distance/2
            out.append((self.by_id[pid], 1.0 - float(dist) / 2.0))
        return out


class Retriever:
    def __init__(self, settings, embedder, passages):
        self.settings = settings
        self.embedder = embedder
        self.passages = passages
        vectors = embedder.encode([p["text"] for p in passages])
        if settings.vector_backend == "chroma":
            name = f"docs_{settings.chunk_strategy}_{embedder.name}".replace("-", "_")
            self.index = ChromaIndex(passages, vectors, settings.storage_dir / "chroma", name)
        else:
            self.index = MemoryIndex(passages, vectors)

    def search(self, text: str, k: int = None, threshold: float = None) -> list:
        """Ranked passages above the relevance threshold. May return an empty list."""
        k = k or self.settings.retrieval_top_k
        threshold = self.settings.relevance_threshold if threshold is None else threshold
        if not text.strip():
            return []
        query_vec = self.embedder.encode([text])[0]
        hits = self.index.search(query_vec, k)
        return [Passage(passage_id=p["passage_id"], doc_id=p["doc_id"], title=p["title"],
                        text=p["text"], score=round(score, 4))
                for p, score in hits if score >= threshold]
