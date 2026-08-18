"""Public retrieval API and Precision@k evaluation."""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any
from .chunking import Chunk, get_chunker
from .data import load_records
from .indexes import BM25Index, DenseIndex, rrf

_QUERY_STOPWORDS = {
    "what", "which", "who", "where", "when", "why", "how", "is", "are", "was", "were",
    "the", "a", "an", "this", "that", "these", "those", "do", "does", "did", "can", "could",
    "tell", "me", "about", "please", "explain", "का", "की", "के", "क्या", "कौन", "कहाँ", "कब", "क्यों",
    "कैसे", "है", "हैं", "में", "और", "को", "से", "यह", "वह", "rag", "pipeline", "document", "documents",
    "retrieval", "retrieve", "retrieves", "relevant", "chunks", "context", "grounded", "answer", "generation",
    "question", "knowledge", "base",
}

def _query_has_support(query: str, chunks: list[Chunk]) -> bool:
    query_terms = set(re.findall(r"[\w\u0900-\u097F]+", query.lower(), flags=re.UNICODE)) - _QUERY_STOPWORDS
    context = " ".join(chunk.chunk_text.lower() for chunk in chunks)
    context_terms = set(re.findall(r"[\w\u0900-\u097F]+", context, flags=re.UNICODE))
    if not query_terms and "rag" in query.lower() and "rag" in context_terms:
        return True
    if not query_terms.intersection(context_terms):
        return False
    return all(term in context_terms for term in query_terms)

@dataclass
class RetrievalConfig:
    strategy: str = "semantic"
    sample_size: int = 5000
    dense_candidates: int = 30
    sparse_candidates: int = 30
    rrf_k: int = 60

class RetrievalSystem:
    def __init__(self, records: list[dict[str, Any]], config: RetrievalConfig | None = None, embedder=None):
        self.records, self.config = records, config or RetrievalConfig(); self.embedder = embedder; self._build()
    @classmethod
    def from_path(cls, path, config=None, embedder=None):
        cfg = config or RetrievalConfig(); return cls(load_records(path, limit=cfg.sample_size), cfg, embedder)
    def _build(self):
        self.chunks: list[Chunk] = get_chunker(self.config.strategy).chunk(self.records)
        self.dense, self.sparse = DenseIndex(self.embedder), BM25Index(); self.dense.build(self.chunks); self.sparse.build(self.chunks)
    def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if not query.strip() or k <= 0: return []
        dense = self.dense.search(query, max(k, self.config.dense_candidates)); sparse = self.sparse.search(query, max(k, self.config.sparse_candidates))
        ranked = rrf(dense, sparse, k=k, rrf_k=self.config.rrf_k)
        selected = [self.chunks[i] for i, _ in ranked]
        if not _query_has_support(query, selected):
            return []
        return [{"chunk_text": self.chunks[i].chunk_text, "score": score, "source_id": self.chunks[i].source_id, "chunk_id": self.chunks[i].chunk_id} for i, score in ranked]
    def precision_at_k(self, queries, k=5):
        relevant_by_query = {}
        for q in queries:
            if int(q.get("is_selected", 0)): relevant_by_query.setdefault(str(q.get("query", "")).strip().lower(), set()).add(str(q["source_id"]))
        vals = []
        for q in queries:
            relevant = relevant_by_query.get(str(q.get("query", "")).strip().lower(), set())
            hits = self.retrieve(q.get("query", ""), k); vals.append(sum(x["source_id"] in relevant for x in hits) / k if k else 0)
        return sum(vals) / len(vals) if vals else 0.0

def compare_strategies(records, queries, k=5):
    return {name: RetrievalSystem(records, RetrievalConfig(strategy=name)).precision_at_k(queries, k) for name in ("fixed", "semantic", "hierarchical")}
