"""Sarvam Bulbul text-to-speech adapter with a safe offline fallback."""
from __future__ import annotations

import base64
import asyncio
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from typing import Any, Callable
from urllib import error, request


@dataclass(frozen=True)
class SpeechResult:
    audio_base64: str | None
    mime_type: str
    language_code: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SarvamTTS:
    """Convert answer text to base64 WAV audio using Bulbul v3.

    ``transport`` is injectable for tests. Without an API key, the adapter
    returns a structured error so the browser can use its local speech
    synthesis fallback instead of failing the whole chatbot response.
    """

    def __init__(self, api_key: str | None = None, *, endpoint: str = "https://api.sarvam.ai/text-to-speech",
                 timeout: float = 15.0, speaker: str = "shubh",
                 transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None):
        self.api_key = api_key or os.getenv("SARVAM_API_SUBSCRIPTION_KEY") or os.getenv("SARVAM_API_KEY")
        self.endpoint, self.timeout, self.speaker, self.transport = endpoint, timeout, speaker, transport

    EDGE_VOICES = {
        "en-IN": "en-IN-NeerjaNeural",
        "hi-IN": "hi-IN-SwaraNeural",
        "kn-IN": "kn-IN-SapnaNeural",
        "mr-IN": "mr-IN-AarohiNeural",
    }

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

    @staticmethod
    def _windows_sapi(text: str, language_code: str) -> str | None:
        """Use an installed Windows SAPI voice when the cloud key is absent."""
        if os.name != "nt":
            return None
        output_path = text_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output, tempfile.NamedTemporaryFile(
                suffix=".txt", mode="w", encoding="utf-8", delete=False
            ) as source:
                output_path, text_path = output.name, source.name
                source.write(text)
            # PowerShell reads the text from a file, avoiding shell-quoting
            # user answer content directly into a command.
            def ps_quote(value: str) -> str:
                return "'" + value.replace("'", "''") + "'"
            out_arg, text_arg, lang_arg = map(ps_quote, (output_path, text_path, language_code))
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$v=$s.GetInstalledVoices() | Where-Object {{$_.VoiceInfo.Culture.Name -eq {lang_arg}}} | Select-Object -First 1; "
                "if (-not $v) { exit 3 }; "
                "$s.SelectVoice($v.VoiceInfo.Name); "
                f"$s.SetOutputToWaveFile({out_arg}); $s.Speak((Get-Content -Raw {text_arg})); $s.Dispose()"
            )
            completed = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                                       capture_output=True, timeout=30)
            if completed.returncode != 0:
                return None
            return base64.b64encode(open(output_path, "rb").read()).decode("ascii")
        except (OSError, subprocess.SubprocessError):
            return None
        finally:
            for path in (output_path, text_path):
                if path:
                    try:
                        os.remove(path)
                    except OSError:
                        pass

    @staticmethod
    def _edge_tts(text: str, language_code: str) -> str | None:
        """Use Microsoft Edge's neural voice service without an API key."""
        voice = SarvamTTS.EDGE_VOICES.get(language_code)
        if not voice:
            return None
        output_path = None
        try:
            # Some bundled Python runtimes expose certifi as a namespace
            # package without ``where()``. Edge TTS only needs a CA bundle.
            import ssl
            import certifi
            if not hasattr(certifi, "where"):
                certifi.where = lambda: ssl.get_default_verify_paths().cafile
            import edge_tts  # type: ignore
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as output:
                output_path = output.name
            async def generate() -> None:
                await edge_tts.Communicate(text, voice).save(output_path)
            asyncio.run(generate())
            return base64.b64encode(open(output_path, "rb").read()).decode("ascii")
        except (ImportError, OSError, RuntimeError, TimeoutError):
            return None
        finally:
            if output_path:
                try:
                    os.remove(output_path)
                except OSError:
                    pass

    def synthesize(self, text: str, *, language_code: str) -> dict[str, Any]:
        clean_text = str(text or "").strip()
        if not clean_text:
            return SpeechResult(None, "audio/wav", language_code, "empty text").to_dict()
        if len(clean_text) > 2500:
            clean_text = clean_text[:2497].rsplit(" ", 1)[0] + "..."
        if not self.api_key and self.transport is None:
            edge_audio = self._edge_tts(clean_text, language_code)
            if edge_audio:
                return SpeechResult(edge_audio, "audio/mpeg", language_code).to_dict()
            local_audio = self._windows_sapi(clean_text, language_code)
            if local_audio:
                return SpeechResult(local_audio, "audio/wav", language_code).to_dict()
        try:
            payload = {"text": clean_text, "target_language_code": language_code,
                       "model": "bulbul:v3", "speaker": self.speaker}
            response = self._request(payload)
            encoded = (response.get("audios") or [None])[0]
            if not encoded:
                raise ValueError("TTS response did not contain audio")
            # Validate the server payload before returning it to the browser.
            base64.b64decode(encoded, validate=True)
            return SpeechResult(str(encoded), "audio/wav", language_code).to_dict()
        except (TimeoutError, error.URLError, error.HTTPError, OSError, ValueError, RuntimeError) as exc:
            return SpeechResult(None, "audio/wav", language_code, str(exc)).to_dict()


_default_tts = SarvamTTS()


def synthesize(text: str, *, language_code: str) -> dict[str, Any]:
    return _default_tts.synthesize(text, language_code=language_code)
