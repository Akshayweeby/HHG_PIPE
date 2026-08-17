from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardrailDecision:
    allowed: bool
    state: str
    reason: str = ""


class InputGuardrails:
    """Small replaceable guardrail layer for topic and safety checks."""

    def __init__(self, topic_terms=None):
        self.topic_terms = set(topic_terms or {"rag", "pipeline", "guardrail", "document", "ज्ञान", "जानकारी"})
        self.unsafe_patterns = [r"\b(password|पासवर्ड)\b", r"\b(hack|हैक|बम|bomb)\b", r"\bapi[_ -]?key\b"]

    def check_off_topic(self, text: str) -> GuardrailDecision:
        # Topic classification is intentionally permissive: harmless questions
        # should reach retrieval/generation. Unsupported questions are handled
        # as NO_EVIDENCE downstream rather than being incorrectly blocked here.
        return GuardrailDecision(True, "ALLOW")

    def check_unsafe(self, text: str) -> GuardrailDecision:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self.unsafe_patterns):
            return GuardrailDecision(False, "BLOCK_UNSAFE", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।")
        return GuardrailDecision(True, "ALLOW")

    def check(self, text: str) -> GuardrailDecision:
        unsafe = self.check_unsafe(text)
        if not unsafe.allowed:
            return unsafe
        return self.check_off_topic(text)

