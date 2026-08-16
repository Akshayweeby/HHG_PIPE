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
        tokens = set(re.findall(r"[a-zA-Z]+|[\u0900-\u097f]+", text.lower()))
        if tokens & self.topic_terms or any(term in text.lower() for term in ("what is", "explain", "कैसे", "क्या")):
            return GuardrailDecision(True, "ALLOW")
        return GuardrailDecision(False, "BLOCK_OFF_TOPIC", "यह सवाल इस डेमो के RAG विषय से बाहर है।")

    def check_unsafe(self, text: str) -> GuardrailDecision:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self.unsafe_patterns):
            return GuardrailDecision(False, "BLOCK_UNSAFE", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।")
        return GuardrailDecision(True, "ALLOW")

    def check(self, text: str) -> GuardrailDecision:
        unsafe = self.check_unsafe(text)
        if not unsafe.allowed:
            return unsafe
        return self.check_off_topic(text)

