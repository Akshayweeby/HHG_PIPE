from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardrailDecision:
    allowed: bool
    state: str
    reason: str = ""


class InputGuardrails:
    """Safety checks with permissive topic handling for multilingual input."""

    def __init__(self, topic_terms=None):
        self.topic_terms = set(topic_terms or {"rag", "pipeline", "guardrail", "document", "ज्ञान", "जानकारी"})
        self.unsafe_patterns = [r"\b(password|पासवर्ड)\b", r"\b(hack|हैक|बम|bomb)\b", r"\bapi[_ -]?key\b"]

    def check_off_topic(self, text: str) -> GuardrailDecision:
        # Unsupported questions are handled as NO_EVIDENCE downstream. This
        # avoids blocking harmless questions merely because their language or
        # wording is not in a small keyword list.
        return GuardrailDecision(True, "ALLOW")

    def check_unsafe(self, text: str) -> GuardrailDecision:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self.unsafe_patterns):
            return GuardrailDecision(False, "BLOCK_UNSAFE", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।")
        return GuardrailDecision(True, "ALLOW")

    def check(self, text: str) -> GuardrailDecision:
        unsafe = self.check_unsafe(text)
        return unsafe if not unsafe.allowed else self.check_off_topic(text)
