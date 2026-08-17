# Hindi RAG retrieval module

Standalone retrieval for English, Hindi, Kannada, Marathi, and code-mixed queries. It has no dependency on STT, LLM, frontend, or pipeline code.

## Run the offline smoke test

```powershell
$py = 'C:\Users\shrad\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m retrieval.demo
& $py -m pytest -q
```

## API

```python
from retrieval.data import load_records
from retrieval.pipeline import RetrievalConfig, RetrievalSystem

records = load_records('msmarco_xi_validation.jsonl', limit=5000)
rag = RetrievalSystem(records, RetrievalConfig(strategy='semantic'))
results = rag.retrieve('भारत की राजधानी क्या है?', k=5)
```

The system normalizes common MSMARCO-XI fields (`passage`, `query`, `is_selected`, `docid`/`id`) and supports JSON, JSONL, and CSV. A dataset may also provide `language`, `language_code`, or `lang`; that value is retained in the normalized record. If Hugging Face `datasets` is installed, `load_records(None)` can load a dataset; pass the exact MSMARCO-XI dataset/config in your integration wrapper if its published identifier differs.

Chunking strategies are `fixed`, `semantic`, and `hierarchical`. Dense retrieval uses a deterministic hashing embedder offline; inject a SentenceTransformer-compatible object with `encode(list[str]) -> numpy.ndarray` for production embeddings. The dense implementation is cosine-normalized inner product and can be replaced by FAISS behind the same `DenseIndex.search` interface. Sparse retrieval is native BM25, and results are combined using RRF.

`compare_strategies(records, queries, k)` returns Precision@k for the three strategies. Queries should carry `source_id` and `is_selected`; evaluation uses selected source IDs as relevant documents.
