"""Supported question and answer languages for the voice assistant."""
from __future__ import annotations

LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "code": "en-IN"},
    "hi": {"name": "Hindi", "native_name": "हिंदी", "code": "hi-IN"},
    "kn": {"name": "Kannada", "native_name": "ಕನ್ನಡ", "code": "kn-IN"},
    "mr": {"name": "Marathi", "native_name": "मराठी", "code": "mr-IN"},
}


def normalize_language(value: str | None) -> str:
    """Return the short language key used by the API and UI."""
    candidate = str(value or "en").strip().lower()
    for key, definition in LANGUAGES.items():
        if candidate in {key, definition["code"].lower()}:
            return key
    return "en"


def language_code(value: str | None) -> str:
    return LANGUAGES[normalize_language(value)]["code"]
