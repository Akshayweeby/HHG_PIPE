"""Citation-aware, context-grounded generation adapter."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable


def _value(chunk: Any, key: str, default: Any = "") -> Any:
    if isinstance(chunk, dict):
        return chunk.get(key, default)
    return getattr(chunk, key, default)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w\u0900-\u097F]+", text.lower(), flags=re.UNICODE))


@dataclass
class GenerationService:
    """Use an injected LLM callable or a safe extractive fallback.

    The callable receives ``(query, context)`` and may return either a string
    or ``{"answer": ..., "citations": [...]}``. The service always filters
    citations to IDs that came from the supplied chunks.
    """

    model: Callable[[str, str], Any] | None = None

    def _context(self, chunks: list[Any]) -> tuple[str, list[str]]:
        lines, ids = [], []
        for i, chunk in enumerate(chunks):
            text = str(_value(chunk, "chunk_text", "")).strip()
            source = _value(chunk, "source_id", "") or _value(chunk, "chunk_id", "") or f"chunk-{i}"
            if text:
                lines.append(f"[{source}] {text}"); ids.append(str(source))
        return "\n".join(lines), ids

    def _fallback(self, query: str, chunks: list[Any]) -> tuple[str, list[str]]:
        if not chunks:
            return "I don't know based on the available context.", []
        query_tokens = _tokens(query)
        ranked = sorted(chunks, key=lambda c: (len(query_tokens & _tokens(str(_value(c, "chunk_text", "")))), float(_value(c, "score", 0.0) or 0.0)), reverse=True)
        best = ranked[0]
        text = str(_value(best, "chunk_text", "")).strip()
        source = str(_value(best, "source_id", "") or _value(best, "chunk_id", ""))
        return text, [source] if source else []

    def generate(self, query: str, chunks: list[Any]) -> dict[str, Any]:
        context, valid_ids = self._context(chunks or [])
        if self.model is None:
            answer, citations = self._fallback(query, chunks or [])
        else:
            prompt = ("Answer only from the supplied context. If it does not support the answer, say you do not know. "
                      "Return concise text and do not invent citations.\n\nContext:\n" + context)
            result = self.model(query, prompt)
            if isinstance(result, dict):
                answer, citations = str(result.get("answer", "")), list(result.get("citations", []))
            else:
                answer, citations = str(result), valid_ids
            citations = [str(x) for x in citations if str(x) in valid_ids]
            if not answer.strip(): answer = "I don't know based on the available context."
        return {"answer": answer, "citations": citations}


_default_generator = GenerationService()


def generate(query: str, chunks: list[Any]) -> dict[str, Any]:
    return _default_generator.generate(query, chunks)
