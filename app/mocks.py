from __future__ import annotations

from typing import List

from .models import GeneratedAnswer, RetrievedChunk, Transcript


class MockTranscriber:
    def transcribe(self, audio: str, scenario: str | None = None) -> Transcript:
        if scenario == "low_confidence" or "low confidence" in audio.lower():
            return Transcript("यह सवाल शायद...", 0.42)
        text = audio.strip() or "RAG pipeline क्या है?"
        return Transcript(text, 0.97)


class MockRetriever:
    def retrieve(self, query: str, k: int = 3) -> List[RetrievedChunk]:
        lower = query.lower()
        if "no evidence" in lower or "unanswerable" in lower or "evidence नहीं" in lower:
            return []
        if "partial" in lower or "आंशिक" in lower:
            return [RetrievedChunk("RAG में retrieval चरण relevant documents खोजता है।", 0.77, "doc-rag-01")]
        return [
            RetrievedChunk("RAG pipeline पहले query के लिए relevant chunks retrieve करता है।", 0.91, "doc-rag-01"),
            RetrievedChunk("फिर retrieved context के आधार पर grounded answer generate किया जाता है।", 0.86, "doc-rag-02"),
        ][:k]


class MockGenerator:
    def generate(self, query: str, chunks: List[RetrievedChunk]) -> GeneratedAnswer:
        lower = query.lower()
        if "generation failure" in lower:
            raise RuntimeError("mock generation unavailable")
        if "hallucinated" in lower or "unsupported" in lower:
            return GeneratedAnswer("RAG हमेशा 100% सही उत्तर देता है और live weather भी बताता है।", ["doc-rag-01"])
        if "invalid citation" in lower:
            return GeneratedAnswer("RAG relevant context से उत्तर बनाता है।", ["missing-source"])
        if "partial" in lower or "आंशिक" in lower:
            return GeneratedAnswer("RAG retrieval करता है और यह हमेशा live data भी देता है।", ["doc-rag-01"])
        return GeneratedAnswer("RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।", [c.source_id for c in chunks])

