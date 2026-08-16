"""Dense and sparse indexes with optional FAISS acceleration."""
from __future__ import annotations
import math, re
from collections import Counter, defaultdict
import numpy as np
from .chunking import Chunk

def tokenize(text: str) -> list[str]: return re.findall(r"[\w\u0900-\u097F]+", text.lower(), flags=re.UNICODE)

class HashEmbeddingModel:
    def __init__(self, dimensions: int = 384): self.dimensions = dimensions
    def encode(self, texts: list[str]) -> np.ndarray:
        a = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for i, text in enumerate(texts):
            for token in tokenize(text): a[i, hash(token) % self.dimensions] += 1
            norm = np.linalg.norm(a[i]); a[i] = a[i] / norm if norm else a[i]
        return a

class DenseIndex:
    def __init__(self, embedder=None): self.embedder = embedder or HashEmbeddingModel(); self.matrix = None; self.chunks = []; self.faiss_index = None
    def build(self, chunks: list[Chunk]):
        self.chunks, self.matrix = chunks, self.embedder.encode([c.chunk_text for c in chunks])
        try:
            import faiss  # type: ignore
            self.faiss_index = faiss.IndexFlatIP(self.matrix.shape[1]); self.faiss_index.add(self.matrix)
        except ImportError: self.faiss_index = None
    def search(self, query: str, k: int):
        if not self.chunks: return []
        vector = self.embedder.encode([query])
        if self.faiss_index is not None:
            scores, ids = self.faiss_index.search(vector, min(k, len(self.chunks)))
            return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
        scores = self.matrix @ vector[0]; ids = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in ids]

class BM25Index:
    def build(self, chunks):
        self.chunks = chunks; self.docs = [tokenize(c.chunk_text) for c in chunks]; self.df = Counter(); self.postings = defaultdict(list)
        for i, doc in enumerate(self.docs):
            for term in set(doc): self.df[term] += 1; self.postings[term].append(i)
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
    def search(self, query, k):
        scores = defaultdict(float); n = len(self.docs); k1, b = 1.5, .75
        for term in tokenize(query):
            if term not in self.df: continue
            idf = math.log(1 + (n - self.df[term] + .5) / (self.df[term] + .5))
            for i in self.postings[term]:
                tf, dl = self.docs[i].count(term), len(self.docs[i])
                scores[i] += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / max(1, self.avgdl)))
        return sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]

def rrf(*ranked_lists, k: int, rrf_k: int = 60):
    fused = defaultdict(float)
    for result in ranked_lists:
        for rank, (idx, _) in enumerate(result, start=1): fused[idx] += 1 / (rrf_k + rank)
    return sorted(fused.items(), key=lambda x: (-x[1], x[0]))[:k]
