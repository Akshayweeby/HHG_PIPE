import unittest
from retrieval.data import mock_records
from retrieval.pipeline import RetrievalConfig, RetrievalSystem, compare_strategies

class RetrievalTests(unittest.TestCase):
    def test_contract_and_languages(self):
        s = RetrievalSystem(mock_records(), RetrievalConfig(strategy="semantic"))
        for query in ["भारत की राजधानी?", "What is the capital of India?", "plants को sunlight क्यों चाहिए?"]:
            result = s.retrieve(query, 3)
            self.assertLessEqual(len(result), 3)
            self.assertTrue(all({"chunk_text", "score", "source_id", "chunk_id"} <= set(x) for x in result))

    def test_unsupported_named_entity_returns_no_results(self):
        s = RetrievalSystem(mock_records(), RetrievalConfig(strategy="semantic"))
        self.assertEqual(s.retrieve("What is Akshay RAG system?", 3), [])

    def test_all_strategies(self):
        records = mock_records()
        queries = [{"query": r["query"], "source_id": r["source_id"], "is_selected": 1} for r in records]
        scores = compare_strategies(records, queries, 3)
        self.assertEqual(set(scores), {"fixed", "semantic", "hierarchical"})
        self.assertTrue(all(0 <= x <= 1 for x in scores.values()))
