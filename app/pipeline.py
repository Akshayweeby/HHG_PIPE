from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timezone
from typing import Callable, List

from .guardrails import InputGuardrails
from .grounding import GroundingChecker
from .mocks import MockGenerator, MockRetriever, MockTranscriber
from .models import AudioInput, PipelineResponse, PipelineState, StageTiming


class PipelineRunner:
    def __init__(self, transcriber=None, guardrails=None, retriever=None, generator=None, grounding=None, timeouts=None):
        self.transcriber = transcriber or MockTranscriber()
        self.guardrails = guardrails or InputGuardrails()
        self.retriever = retriever or MockRetriever()
        self.generator = generator or MockGenerator()
        self.grounding = grounding or GroundingChecker()
        self.timeouts = {"STT": 2.0, "guardrails": 1.0, "retrieval": 2.0, "generation": 2.0, "grounding": 1.0, **(timeouts or {})}

    def _stage(self, name: str, fn: Callable, timings: List[StageTiming]):
        start_time = time.perf_counter(); start = datetime.now(timezone.utc).isoformat()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                value = executor.submit(fn).result(timeout=self.timeouts[name])
            return value, None
        except TimeoutError:
            return None, f"{name} timed out"
        except Exception as exc:
            return None, f"{name} failed: {exc}"
        finally:
            timings.append(StageTiming(name, start, datetime.now(timezone.utc).isoformat(), round((time.perf_counter() - start_time) * 1000, 2)))

    def run(self, request: AudioInput) -> PipelineResponse:
        timings: List[StageTiming] = []
        total_start = time.perf_counter(); total_iso = datetime.now(timezone.utc).isoformat()
        transcript, error = self._stage("STT", lambda: self.transcriber.transcribe(request.audio, request.demo_scenario), timings)
        if error:
            return self._finish(PipelineResponse(PipelineState.ERROR, reason=error, error=error), timings, total_start, total_iso)
        if transcript.confidence < 0.70:
            return self._finish(PipelineResponse(PipelineState.REPEAT_LOW_CONFIDENCE, transcript=transcript, reason="आवाज़ स्पष्ट नहीं है। कृपया दोबारा बोलें।"), timings, total_start, total_iso)
        decision, error = self._stage("guardrails", lambda: self.guardrails.check(transcript.text), timings)
        if error:
            return self._finish(PipelineResponse(PipelineState.ERROR, transcript=transcript, reason=error, error=error), timings, total_start, total_iso)
        if not decision.allowed:
            return self._finish(PipelineResponse(PipelineState(decision.state), transcript=transcript, reason=decision.reason), timings, total_start, total_iso)
        chunks, error = self._stage("retrieval", lambda: self.retriever.retrieve(transcript.text, 3), timings)
        if error:
            return self._finish(PipelineResponse(PipelineState.NO_EVIDENCE, transcript=transcript, answer="मुझे नहीं पता।", reason="प्रमाण उपलब्ध नहीं है। मैं इस प्रश्न का उत्तर नहीं दे सकता।", error=error), timings, total_start, total_iso)
        if not chunks:
            return self._finish(PipelineResponse(PipelineState.NO_EVIDENCE, transcript=transcript, answer="मुझे नहीं पता।", reason="प्रमाण उपलब्ध नहीं है। मैं इस प्रश्न का उत्तर नहीं दे सकता।"), timings, total_start, total_iso)
        generated, error = self._stage("generation", lambda: self.generator.generate(transcript.text, chunks), timings)
        if error:
            return self._finish(PipelineResponse(PipelineState.ERROR, transcript=transcript, reason="उत्तर बनाते समय समस्या हुई।", error=error), timings, total_start, total_iso)
        grounding, error = self._stage("grounding", lambda: self.grounding.check(generated.answer, generated.citations, chunks), timings)
        if error:
            return self._finish(PipelineResponse(PipelineState.GROUNDING_FAILED, transcript=transcript, reason=error), timings, total_start, total_iso)
        signals = grounding["signals"]
        if not grounding["grounded"]:
            response = PipelineResponse(PipelineState.GROUNDING_FAILED, transcript, "मुझे इस उत्तर के लिए पर्याप्त प्रमाण नहीं मिला।", generated.citations, grounding["reason"], signals)
        else:
            response = PipelineResponse(PipelineState.ALLOW, transcript, generated.answer, generated.citations, grounding["reason"], signals)
        return self._finish(response, timings, total_start, total_iso)

    def _finish(self, response, timings, total_start, total_iso):
        timings.append(StageTiming("total", total_iso, datetime.now(timezone.utc).isoformat(), round((time.perf_counter() - total_start) * 1000, 2)))
        response.timings = timings
        return response

