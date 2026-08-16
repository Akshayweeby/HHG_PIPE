"""Dataset loading and normalization for MSMARCO-XI style records."""
from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any

def _first(record: dict[str, Any], names: tuple[str, ...], default: Any = "") -> Any:
    for name in names:
        if name in record and record[name] not in (None, ""):
            return record[name]
    return default

def normalize_record(record: dict[str, Any], row_id: int) -> dict[str, Any]:
    text = str(_first(record, ("passage", "text", "context", "document", "contents")))
    query = str(_first(record, ("query", "question", "query_text")))
    selected = _first(record, ("is_selected", "label", "relevant", "relevance"), 0)
    try:
        selected = int(bool(int(selected))) if not isinstance(selected, bool) else int(selected)
    except (TypeError, ValueError):
        selected = int(str(selected).lower() in {"true", "yes", "relevant"})
    return {"source_id": str(_first(record, ("source_id", "docid", "document_id", "passage_id", "id"), row_id)),
            "query": query, "passage": text, "is_selected": selected,
            "title": str(_first(record, ("title", "document_title"), "")), "metadata": record}

def load_records(path: str | Path | None = None, *, dataset_name: str = "microsoft/ms_marco",
                 split: str = "validation", limit: int = 5000) -> list[dict[str, Any]]:
    """Load local JSON/JSONL/CSV, or a Hugging Face dataset when path is None."""
    if path is None:
        try:
            from datasets import load_dataset  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install datasets or pass a local --data file") from exc
        ds = load_dataset(dataset_name, split=split)
        return [normalize_record(dict(row), i) for i, row in enumerate(ds.select(range(min(limit, len(ds)))))]
    p = Path(path)
    if p.suffix.lower() in {".jsonl", ".ndjson"}:
        rows = (json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
    elif p.suffix.lower() == ".json":
        raw = json.loads(p.read_text(encoding="utf-8")); rows = raw if isinstance(raw, list) else raw.get("data", raw.get("records", []))
    elif p.suffix.lower() == ".csv":
        rows = csv.DictReader(p.open(encoding="utf-8-sig", newline=""))
    else:
        raise ValueError(f"Unsupported dataset format: {p.suffix}")
    return [normalize_record(dict(row), i) for i, row in enumerate(rows)][:limit]

def mock_records() -> list[dict[str, Any]]:
    rows = [("doc-1", "भारत की राजधानी नई दिल्ली है।", "भारत की राजधानी क्या है?"),
            ("doc-2", "जल चक्र में वाष्पीकरण, संघनन और वर्षण शामिल हैं।", "water cycle में कौन से चरण होते हैं?"),
            ("doc-3", "The sun is a star at the center of the solar system.", "What is at the center of solar system?"),
            ("doc-4", "पौधों में प्रकाश संश्लेषण के लिए सूर्य का प्रकाश आवश्यक है।", "plants को sunlight क्यों चाहिए?"),
            ("doc-5", "भारत का संविधान नागरिकों को मौलिक अधिकार देता है।", "fundamental rights किससे मिलते हैं?")]
    return [{"source_id": s, "passage": p, "query": q, "is_selected": 1, "title": "", "metadata": {}} for s, p, q in rows]
