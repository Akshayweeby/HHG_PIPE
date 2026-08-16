# Guardrails + Pipeline + Frontend

Self-contained Hindi voice-enabled RAG harness using deterministic mocks. The pipeline is intentionally conservative: unsupported or weakly cited answers become `GROUNDING_FAILED` / “I don’t know”.

## Run

Requires Python 3.10+ and no third-party packages.

```powershell
python server.py
```

Open http://127.0.0.1:8000. The microphone button uses browser speech recognition when available; typed demo scenarios work everywhere.

## Test and evaluate

```powershell
python -m unittest discover -s tests -v
python -c "from app.evaluation import run_evaluation; import json; print(json.dumps(run_evaluation(), ensure_ascii=False, indent=2))"
```

## Architecture

`PipelineRunner` depends on replaceable interfaces: `transcribe(audio, scenario)`, `check(text)`, `retrieve(query, k)`, `generate(query, chunks)`, and `check(answer, citations, chunks)`. Each stage returns typed dataclasses where practical, records UTC timestamps and duration, and has an independent timeout/fallback.

Mocks live in `app/mocks.py`; replace those classes with real STT, retrieval, and generation adapters without changing the runner. Grounding keeps embedding similarity, self-critique, and citation validity separately observable. Configure its policy in `app/grounding.py`.

