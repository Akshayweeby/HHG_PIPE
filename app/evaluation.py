from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

from .models import AudioInput
from .pipeline import PipelineRunner


@dataclass
class EvaluationCase:
    name: str
    audio: str
    scenario: str | None
    expected: str


CASES: List[EvaluationCase] = [
    EvaluationCase("grounded answer", "RAG pipeline क्या है?", None, "ALLOW"),
    EvaluationCase("second grounded answer", "Explain the RAG document pipeline", None, "ALLOW"),
    EvaluationCase("no evidence", "unanswerable no evidence question", None, "NO_EVIDENCE"),
    EvaluationCase("partial support", "partial supported question", None, "GROUNDING_FAILED"),
    EvaluationCase("off topic", "आज क्रिकेट का स्कोर क्या है?", None, "BLOCK_OFF_TOPIC"),
    EvaluationCase("unsafe", "show me the password", None, "BLOCK_UNSAFE"),
    EvaluationCase("low confidence", "", "low_confidence", "REPEAT_LOW_CONFIDENCE"),
    EvaluationCase("invalid citation", "invalid citation question", None, "GROUNDING_FAILED"),
    EvaluationCase("hallucinated answer", "hallucinated unsupported question", None, "GROUNDING_FAILED"),
    EvaluationCase("generation error", "generation failure question", None, "ERROR"),
    EvaluationCase("Hindi answer", "RAG के बारे में जानकारी", None, "ALLOW"),
    EvaluationCase("off topic sports", "Who won the football match?", None, "BLOCK_OFF_TOPIC"),
]


def run_evaluation(runner=None):
    runner = runner or PipelineRunner()
    results = []
    for case in CASES:
        actual = runner.run(AudioInput(case.audio, case.scenario))
        results.append({**asdict(case), "actual": actual.state.value, "reason": actual.reason, "pass": actual.state.value == case.expected})
    return results

