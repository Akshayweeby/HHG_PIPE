from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.models import AudioInput
from app.pipeline import PipelineRunner
from voice.answer_language import AnswerLanguageAdapter

ROOT = Path(__file__).parent
runner = PipelineRunner()
answer_language = AnswerLanguageAdapter()


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
            question_language = str(payload.get("question_language", "en")).lower()
            if question_language not in {"hi", "en"}:
                question_language = "en"
            result = runner.run(AudioInput(str(payload.get("audio", "")), payload.get("demo_scenario"))).to_dict()
            if result.get("state") == "ALLOW" and result.get("answer"):
                result.update(answer_language.translate_answer(result["answer"], question_language))
            else:
                result["answer_language"] = answer_language.target_for(question_language)
            return self._send(200, result)
        except Exception as exc:
            return self._send(400, {"error": str(exc)})

    def log_message(self, *_):
        return


if __name__ == "__main__":
    print("Guardrails demo running at http://127.0.0.1:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

