"""Fixed, semantic, and metadata-aware chunkers."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Chunk:
    chunk_text: str
    source_id: str
    chunk_id: str
    metadata: dict[str, Any]

def _sentences(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"(?<=[.!?।॥])\s+|\n+", text) if x.strip()]

class FixedSizeChunker:
    def __init__(self, size: int = 180, overlap: int = 40):
        if size <= 0 or not 0 <= overlap < size: raise ValueError("require size > overlap >= 0")
        self.size, self.overlap = size, overlap
    def chunk(self, records):
        out, step = [], self.size - self.overlap
        for r in records:
            for i, start in enumerate(range(0, len(r["passage"]), step)):
                piece = r["passage"][start:start + self.size].strip()
                if piece: out.append(Chunk(piece, str(r["source_id"]), f"{r['source_id']}-f{i}", r.get("metadata", {})))
        return out

class SemanticChunker:
    def __init__(self, max_chars: int = 360): self.max_chars = max_chars
    def chunk(self, records):
        out = []
        for r in records:
            groups, current = [], ""
            for sentence in _sentences(r["passage"]):
                if current and len(current) + len(sentence) + 1 > self.max_chars: groups.append(current); current = ""
                current = f"{current} {sentence}".strip()
            if current: groups.append(current)
            if not groups and r["passage"].strip(): groups = [r["passage"].strip()]
            out.extend(Chunk(x, str(r["source_id"]), f"{r['source_id']}-s{i}", r.get("metadata", {})) for i, x in enumerate(groups))
        return out

class HierarchicalChunker:
    def __init__(self, max_chars: int = 420): self.max_chars = max_chars
    def chunk(self, records):
        out = []
        for r in records:
            title = r.get("title", "") or r.get("metadata", {}).get("title", "")
            text = (f"{title}: " if title else "") + r["passage"]
            for i, piece in enumerate(filter(None, (text[x:x+self.max_chars].strip() for x in range(0, len(text), self.max_chars)))):
                meta = dict(r.get("metadata", {})); meta.update({"title": title, "parent_source_id": str(r["source_id"]), "level": "leaf"})
                out.append(Chunk(piece, str(r["source_id"]), f"{r['source_id']}-h{i}", meta))
        return out

def get_chunker(name: str):
    return {"fixed": FixedSizeChunker, "semantic": SemanticChunker, "hierarchical": HierarchicalChunker}[name]()
