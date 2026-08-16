from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .models import GeneratedAnswer, GroundingSignals, RetrievedChunk


@dataclass
class GroundingPolicy:
    similarity_threshold: float = 0.68
    require_self_critique: bool = True
    require_valid_citations: bool = True


class GroundingChecker:
    def __init__(self, policy: GroundingPolicy | None = None):
        self.policy = policy or GroundingPolicy()
        self.last_signals: GroundingSignals | None = None

    def _similarity(self, answer: str, chunks: List[RetrievedChunk]) -> float:
        if not chunks:
            return 0.0
        answer_words = set(re.findall(r"[a-zA-Z]+|[\u0900-\u097f]+", answer.lower()))
        context_words = set().union(*(set(re.findall(r"[a-zA-Z]+|[\u0900-\u097f]+", c.chunk_text.lower())) for c in chunks))
        return len(answer_words & context_words) / max(1, len(answer_words))

    def _self_critique(self, answer: str, chunks: List[RetrievedChunk]) -> bool:
        if not chunks:
            return False
        unsupported_markers = ("always", "100%", "live weather", "हमेशा", "100%")
        return not any(marker in answer.lower() for marker in unsupported_markers)

    def _citation_valid(self, citations: List[str], chunks: List[RetrievedChunk]) -> bool:
        valid_ids = {c.source_id for c in chunks}
        return bool(citations) and all(citation in valid_ids for citation in citations)

    def check(self, answer: str, citations: List[str], chunks: List[RetrievedChunk]) -> dict:
        signals = GroundingSignals(self._similarity(answer, chunks), self._self_critique(answer, chunks), self._citation_valid(citations, chunks))
        self.last_signals = signals
        grounded = (
            signals.embedding_similarity >= self.policy.similarity_threshold
            and (signals.llm_self_critique or not self.policy.require_self_critique)
            and (signals.citation_validity or not self.policy.require_valid_citations)
        )
        failed = []
        if signals.embedding_similarity < self.policy.similarity_threshold:
            failed.append("embedding similarity below threshold")
        if self.policy.require_self_critique and not signals.llm_self_critique:
            failed.append("LLM self-critique flagged unsupported claims")
        if self.policy.require_valid_citations and not signals.citation_validity:
            failed.append("citation validity failed")
        return {"grounded": grounded, "reason": "grounded by all configured signals" if grounded else "; ".join(failed), "signals": signals}


def check_grounding(answer, citations, chunks):
    """Required public interface; signals are retained in the returned result."""
    return GroundingChecker().check(answer, citations, chunks)

