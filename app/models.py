from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class PipelineState(str, Enum):
    ALLOW = "ALLOW"
    BLOCK_OFF_TOPIC = "BLOCK_OFF_TOPIC"
    BLOCK_UNSAFE = "BLOCK_UNSAFE"
    REPEAT_LOW_CONFIDENCE = "REPEAT_LOW_CONFIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"
    GROUNDING_FAILED = "GROUNDING_FAILED"
    ERROR = "ERROR"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AudioInput:
    audio: str = ""
    demo_scenario: Optional[str] = None


@dataclass
class Transcript:
    text: str
    confidence: float


@dataclass
class RetrievedChunk:
    chunk_text: str
    score: float
    source_id: str


@dataclass
class GeneratedAnswer:
    answer: str
    citations: List[str]


@dataclass
class GroundingSignals:
    embedding_similarity: float
    llm_self_critique: bool
    citation_validity: bool


@dataclass
class StageTiming:
    stage: str
    start: str
    end: str
    duration_ms: float


@dataclass
class PipelineResponse:
    state: PipelineState
    transcript: Optional[Transcript] = None
    answer: str = ""
    citations: List[str] = field(default_factory=list)
    reason: str = ""
    grounding: Optional[GroundingSignals] = None
    timings: List[StageTiming] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        value["transcript"] = asdict(self.transcript) if self.transcript else None
        return value

