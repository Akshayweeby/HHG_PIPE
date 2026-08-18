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
UI_ROOT = ROOT / "frontend" if (ROOT / "frontend").exists() else ROOT / "static"
runner = PipelineRunner()
answer_language = AnswerLanguageAdapter()
tts = SarvamTTS()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else (json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, (dict, list)) else payload.encode())
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body))); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.end_headers(); self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            return self._send(200, {"ok": True})
        if self.path in ("/", "/index.html"):
            return self._send(200, (UI_ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        static = {"/styles.css": ("styles.css", "text/css"), "/app.js": ("app.js", "text/javascript")}
        if self.path in static:
            name, content_type = static[self.path]
            return self._send(200, (UI_ROOT / name).read_bytes(), content_type)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/pipeline":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0)); payload = json.loads(self.rfile.read(length) or b"{}")
            question_language = normalize_language(payload.get("question_language", "en"))
            answer_language_key = normalize_language(payload.get("answer_language", question_language))
            result = runner.run(AudioInput(str(payload.get("audio", "")), payload.get("demo_scenario"))).to_dict()
            if result.get("answer"):
                result.update(answer_language.translate_answer(result["answer"], answer_language_key))
            else:
                result["answer_language"] = answer_language.target_for(answer_language_key)
            if result.get("reason"):
                translated_reason = answer_language.translate_answer(result["reason"], answer_language_key)
                if not translated_reason.get("translation_error"):
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
    import os

    port = int(os.environ.get("PORT", 8000))

    print(f"Guardrails demo running on port {port}")

    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
