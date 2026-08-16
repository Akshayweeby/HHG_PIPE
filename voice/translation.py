"""Sarvam text translation adapter for Hindi, English, and code-mixed input."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Any, Callable
from urllib import error, request


@dataclass(frozen=True)
class TranslationResult:
    original_text: str
    translated_text: str
    source_language_code: str
    target_language_code: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sentence_parts(text: str, limit: int = 1900) -> list[str]:
    parts, current = [], ""
    for sentence in text.replace("\r\n", "\n").splitlines():
        for piece in sentence.split("।"):
            piece = piece.strip()
            if not piece:
                continue
            piece = piece + "।"
            if current and len(current) + len(piece) > limit:
                parts.append(current); current = ""
            current += (" " if current else "") + piece
    if current: parts.append(current)
    return parts or [text[:limit]]


class SarvamTranslator:
    """Translate text through Sarvam's ``/translate`` endpoint.

    A callable ``transport`` can be injected in tests. The API key is read
    from ``SARVAM_API_SUBSCRIPTION_KEY`` or ``SARVAM_API_KEY``.
    """

    def __init__(self, api_key: str | None = None, *, endpoint: str = "https://api.sarvam.ai/translate",
                 timeout: float = 15.0, retries: int = 2,
                 transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None):
        self.api_key = api_key or os.getenv("SARVAM_API_SUBSCRIPTION_KEY") or os.getenv("SARVAM_API_KEY")
        self.endpoint, self.timeout, self.retries, self.transport = endpoint, timeout, max(0, retries), transport

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(payload)
        if not self.api_key:
            raise RuntimeError("SARVAM_API_SUBSCRIPTION_KEY is not configured")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(self.endpoint, data=body, method="POST", headers={
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        with request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def translate(self, text: str, *, source_language_code: str = "auto",
                  target_language_code: str = "hi-IN", mode: str = "code-mixed") -> dict[str, Any]:
        original = str(text or "").strip()
        if not original:
            return TranslationResult("", "", source_language_code, target_language_code, "empty text").to_dict()
        translated: list[str] = []
        detected = source_language_code
        try:
            for part in _sentence_parts(original):
                payload = {"input": part, "source_language_code": source_language_code,
                           "target_language_code": target_language_code, "mode": mode, "model": "mayura:v1"}
                last_error = None
                for attempt in range(self.retries + 1):
                    try:
                        response = self._request(payload)
                        translated.append(str(response.get("translated_text", "")))
                        detected = str(response.get("source_language_code", detected))
                        last_error = None
                        break
                    except (TimeoutError, error.URLError, error.HTTPError, OSError, ValueError, RuntimeError) as exc:
                        last_error = str(exc)
                        if attempt < self.retries: time.sleep(min(.25 * (2 ** attempt), 1.0))
                if last_error: raise RuntimeError(last_error)
            return TranslationResult(original, " ".join(x for x in translated if x), detected, target_language_code).to_dict()
        except Exception as exc:
            return TranslationResult(original, original, detected, target_language_code, str(exc)).to_dict()


_default_translator = SarvamTranslator()


def translate(text: str, *, source_language_code: str = "auto", target_language_code: str = "hi-IN") -> dict[str, Any]:
    return _default_translator.translate(text, source_language_code=source_language_code, target_language_code=target_language_code)
