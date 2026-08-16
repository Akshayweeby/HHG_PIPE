"""Sarvam Hindi speech-to-text adapter with retries and quality handling.

The public ``transcribe`` function is dependency-free and does not require a
real API key in tests. Inject ``transport`` with a callable returning the
Sarvam JSON response to mock the network boundary.
"""
from __future__ import annotations

import io
import mimetypes
import os
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable
from urllib import error, request


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    confidence: float
    reliable: bool
    should_repeat: bool
    language_code: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _audio_bytes(audio: Any) -> tuple[bytes, str, str]:
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio), "audio.wav", "audio/wav"
    if hasattr(audio, "read"):
        data = audio.read()
        return data, getattr(audio, "name", "audio.wav"), "audio/wav"
    path = Path(str(audio))
    data = path.read_bytes()
    return data, path.name, mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def _multipart(audio: Any) -> tuple[bytes, str]:
    data, filename, content_type = _audio_bytes(audio)
    boundary = "----CodexSarvam" + uuid.uuid4().hex
    prefix = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n"
    ).encode()
    return prefix + data + f"\r\n--{boundary}--\r\n".encode(), boundary


class SarvamSTT:
    """Small synchronous Sarvam REST client.

    ``confidence`` is Sarvam's ``language_probability`` quality signal when
    present; it is intentionally not presented as transcription accuracy.
    """

    def __init__(self, api_key: str | None = None, *, endpoint: str = "https://api.sarvam.ai/speech-to-text",
                 timeout: float = 15.0, retries: int = 2, min_confidence: float = 0.70,
                 transport: Callable[[Any], dict[str, Any]] | None = None):
        self.api_key = api_key or os.getenv("SARVAM_API_SUBSCRIPTION_KEY") or os.getenv("SARVAM_API_KEY")
        self.endpoint, self.timeout = endpoint, timeout
        self.retries, self.min_confidence, self.transport = max(0, retries), min_confidence, transport

    def _request(self, audio: Any) -> dict[str, Any]:
        if self.transport is not None:
            return self.transport(audio)
        if not self.api_key:
            raise RuntimeError("SARVAM_API_SUBSCRIPTION_KEY is not configured")
        body, boundary = _multipart(audio)
        req = request.Request(self.endpoint, data=body, method="POST", headers={
            "api-subscription-key": self.api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        })
        with request.urlopen(req, timeout=self.timeout) as response:
            import json
            return json.loads(response.read().decode("utf-8"))

    def transcribe_result(self, audio: Any) -> TranscriptionResult:
        if audio is None or (isinstance(audio, str) and not audio.strip()):
            return TranscriptionResult("", 0.0, False, True, error="empty audio input")
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                payload = self._request(audio)
                text = str(payload.get("transcript") or "").strip()
                confidence = float(payload.get("language_probability", 0.0) or 0.0)
                language = payload.get("language_code")
                reliable = bool(text) and len("".join(text.split("."))) >= 2 and confidence >= self.min_confidence
                return TranscriptionResult(text, confidence, reliable, not reliable, language)
            except (TimeoutError, error.URLError, error.HTTPError, OSError, ValueError, RuntimeError) as exc:
                last_error = str(exc)
                if attempt < self.retries:
                    time.sleep(min(0.25 * (2 ** attempt), 1.0))
        return TranscriptionResult("", 0.0, False, True, error=last_error or "STT request failed")

    def transcribe(self, audio: Any) -> dict[str, Any]:
        """Return the stable dict contract expected by the integration layer."""
        return self.transcribe_result(audio).to_dict()


_default_stt = SarvamSTT()


def transcribe(audio: Any) -> dict[str, Any]:
    return _default_stt.transcribe(audio)
