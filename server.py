from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.models import AudioInput
from app.pipeline import PipelineRunner
from voice.answer_language import AnswerLanguageAdapter
from voice.languages import normalize_language
from voice.tts import SarvamTTS

ROOT = Path(__file__).parent
runner = PipelineRunner()
answer_language = AnswerLanguageAdapter()
tts = SarvamTTS()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else (json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, (dict, list)) else payload.encode())
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self._send(200, {"ok": True})
        if self.path in ("/", "/index.html"):
            return self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html; charset=utf-8")
        static = {"/styles.css": ("styles.css", "text/css"), "/app.js": ("app.js", "text/javascript")}
        if self.path in static:
            name, content_type = static[self.path]
            return self._send(200, (ROOT / "static" / name).read_bytes(), content_type)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/pipeline":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0)); payload = json.loads(self.rfile.read(length) or b"{}")
            # The selected response language is independent from the language
            # used to ask the question. Keep question_language as a backward-
            # compatible alias for existing clients.
            response_language = normalize_language(
                payload.get("answer_language", payload.get("question_language", "en"))
            )
            result = runner.run(AudioInput(str(payload.get("audio", "")), payload.get("demo_scenario"))).to_dict()
            if result.get("answer"):
                result.update(answer_language.translate_answer(result["answer"], response_language))
            else:
                result["answer_language"] = answer_language.target_for(response_language)
            if result.get("reason"):
                translated_reason = answer_language.translate_answer(result["reason"], response_language)
                result["reason"] = translated_reason["answer"]
            if result.get("answer") and payload.get("speak_answer", True):
                result["answer_audio"] = tts.synthesize(
                    result["answer"], language_code=result["answer_language"]
                )
            return self._send(200, result)
        except Exception as exc:
            return self._send(400, {"error": str(exc)})

    def log_message(self, *_):
        return


if __name__ == "__main__":
    print("Guardrails demo running at http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

