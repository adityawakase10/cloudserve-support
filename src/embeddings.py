# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Embeddings: turn text into vectors so similar meanings sit close together.

Two interchangeable backends:
- sentence-transformers (default): the all-MiniLM-L6-v2 model from Hugging Face.
  Understands meaning, so "my deployment keeps dying" can match
  "resolving container health check failures".
- tfidf: word-overlap vectors from scikit-learn. No model download, used for
  fast tests and CI. Weaker: only matches shared words.

Both return unit-length vectors, so cosine similarity = dot product.
"""
import numpy as np


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer   # imported lazily: heavy
        self.model = SentenceTransformer(model_name)

    def fit(self, corpus):                                       # pre-trained, nothing to fit
        return self

    def encode(self, texts) -> np.ndarray:
        return self.model.encode(list(texts), normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)


class TfidfEmbedder:
    name = "tfidf"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        self._fitted = False

    def fit(self, corpus):
        self.vectorizer.fit(list(corpus))
        self._fitted = True
        return self

    def encode(self, texts) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("TfidfEmbedder must be fitted before encoding")
        matrix = self.vectorizer.transform(list(texts)).toarray().astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / np.where(norms == 0, 1, norms)


_cache = {}


def get_embedder(backend: str, model_name: str, corpus=None):
    """One embedder per backend per process (loading MiniLM takes a few seconds)."""
    key = (backend, model_name)
    if key not in _cache:
        if backend == "tfidf":
            if corpus is None:
                raise ValueError("tfidf backend needs a corpus to fit on")
            _cache[key] = TfidfEmbedder().fit(corpus)
        else:
            _cache[key] = SentenceTransformerEmbedder(model_name)
    return _cache[key]
