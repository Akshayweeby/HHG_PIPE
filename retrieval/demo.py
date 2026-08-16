import sys
from .data import mock_records
from .pipeline import RetrievalConfig, RetrievalSystem, compare_strategies

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    records = mock_records(); system = RetrievalSystem(records, RetrievalConfig(strategy="semantic"))
    for query in [r["query"] for r in records[:3]]: print(query, "->", system.retrieve(query, 3))
    queries = [{"query": r["query"], "source_id": r["source_id"], "is_selected": 1} for r in records]
    print("Precision@3:", compare_strategies(records, queries, 3))
