"""Plug-in voice/STT and generation components for the Hindi RAG system."""

from .generation import GenerationService, generate
from .stt import SarvamSTT, TranscriptionResult, transcribe
from .translation import SarvamTranslator, TranslationResult, translate
from .answer_language import AnswerLanguageAdapter
from .tts import SarvamTTS, SpeechResult, synthesize

__all__ = ["AnswerLanguageAdapter", "GenerationService", "SarvamSTT", "TranscriptionResult", "SarvamTranslator", "TranslationResult", "SarvamTTS", "SpeechResult", "generate", "synthesize", "transcribe", "translate"]
