# Voice/STT and generation modules

`voice.stt` exposes `transcribe(audio) -> dict`. It uses Sarvam's synchronous `/speech-to-text` REST endpoint when `SARVAM_API_SUBSCRIPTION_KEY` (or `SARVAM_API_KEY`) is configured. The response's `language_probability` is preserved as a quality signal, not mislabeled as transcription accuracy. Tests inject a transport mock.

`voice.generation` exposes `generate(query, chunks) -> {answer, citations}`. It has a safe extractive fallback for offline use and accepts an injected model callable for a real LLM. Citations are restricted to source/chunk IDs present in retrieved context.
