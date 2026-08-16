# Retrieval subsystem

Standalone Hindi/Hinglish retrieval. It supports fixed-overlap, semantic, and hierarchical chunking; injectable embeddings; optional FAISS dense retrieval; BM25 sparse retrieval; RRF fusion; and Precision@k evaluation.

```python
from retrieval.data import load_records
from retrieval.pipeline import RetrievalConfig, RetrievalSystem

records = load_records("msmarco_xi_validation.jsonl", limit=5000)
rag = RetrievalSystem(records, RetrievalConfig(strategy="semantic"))
results = rag.retrieve("भारत की राजधानी क्या है?", k=5)
```

For production, install `numpy`, `faiss-cpu`, and optionally `datasets` plus a SentenceTransformer-compatible embedding model. Without FAISS/model packages, deterministic local fallbacks keep the module runnable for tests.
