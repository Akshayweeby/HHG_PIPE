# Voice/STT, generation, translation, and answer speech modules

`voice.stt` exposes `transcribe(audio) -> dict`. It uses Sarvam's synchronous `/speech-to-text` REST endpoint when `SARVAM_API_SUBSCRIPTION_KEY` (or `SARVAM_API_KEY`) is configured. The response's `language_probability` is preserved as a quality signal, not mislabeled as transcription accuracy. Tests inject a transport mock.

`voice.generation` exposes `generate(query, chunks) -> {answer, citations}`. It has a safe extractive fallback for offline use and accepts an injected model callable for a real LLM. Citations are restricted to source/chunk IDs present in retrieved context.

`voice.translation` exposes `translate(text)`. It uses Sarvam Mayura with automatic source-language detection and code-mixed mode, preserving the original text while returning normalized Hindi output. Text is split at sentence boundaries under the API request limit. [Sarvam translation API](https://docs.sarvam.ai/api-reference/text/translate-text)

`voice.tts` exposes `synthesize(text, language_code=...)`. It prefers Sarvam Bulbul v3 when configured; otherwise it uses Microsoft Edge neural voices without requiring an API key (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`, `kn-IN-SapnaNeural`, and `mr-IN-AarohiNeural`). Audio is returned as base64 MP3/WAV. If both services are unavailable, the web client uses a matching installed browser voice and clearly reports when that voice is unavailable.

The web pipeline accepts `en`, `hi`, `kn`, and `mr` (or their BCP-47 codes). Answers and answer audio always use the selected question language. The browser fallback also selects a matching installed voice when the server-side audio is unavailable.
