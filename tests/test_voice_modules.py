import unittest

from voice.generation import GenerationService
from voice.stt import SarvamSTT
from voice.translation import SarvamTranslator
from voice.answer_language import AnswerLanguageAdapter


class TestVoiceModules(unittest.TestCase):
    def test_stt_success(self):
        stt = SarvamSTT(transport=lambda _: {"transcript": "भारत की राजधानी क्या है?", "language_probability": 0.96, "language_code": "hi-IN"})
        result = stt.transcribe(b"mock-audio")
        self.assertEqual(result["text"], "भारत की राजधानी क्या है?")
        self.assertTrue(result["reliable"]); self.assertFalse(result["should_repeat"])

    def test_stt_empty_and_low_quality(self):
        empty = SarvamSTT(transport=lambda _: {"transcript": "", "language_probability": 0.99}).transcribe(b"audio")
        low = SarvamSTT(transport=lambda _: {"transcript": "........", "language_probability": 0.40}).transcribe(b"audio")
        self.assertTrue(empty["should_repeat"]); self.assertTrue(low["should_repeat"])

    def test_stt_timeout_retry(self):
        calls = []
        def failing(_):
            calls.append(1); raise TimeoutError("timed out")
        result = SarvamSTT(transport=failing, retries=2).transcribe(b"audio")
        self.assertEqual(len(calls), 3); self.assertTrue(result["should_repeat"]); self.assertIn("timed out", result["error"])

    def test_generation_context_and_citations(self):
        result = GenerationService().generate("भारत में सौर ऊर्जा क्या है?", [{"chunk_text": "भारत में सौर ऊर्जा एक नवीकरणीय ऊर्जा स्रोत है।", "score": .91, "source_id": "chunk_001"}])
        self.assertIn("सौर ऊर्जा", result["answer"]); self.assertEqual(result["citations"], ["chunk_001"])

    def test_generation_insufficient_context(self):
        result = GenerationService().generate("What is the capital?", [])
        self.assertEqual(result["citations"], []); self.assertIn("don't know", result["answer"])

    def test_model_citations_are_restricted_to_context(self):
        service = GenerationService(model=lambda q, p: {"answer": "Delhi", "citations": ["valid", "invented"]})
        result = service.generate("capital?", [{"chunk_text": "Delhi is the capital.", "source_id": "valid"}])
        self.assertEqual(result["citations"], ["valid"])

    def test_translation_mock(self):
        translator = SarvamTranslator(transport=lambda payload: {"translated_text": "भारत की राजधानी क्या है?", "source_language_code": "en-IN"})
        result = translator.translate("What is the capital of India?")
        self.assertEqual(result["translated_text"], "भारत की राजधानी क्या है?")
        self.assertEqual(result["source_language_code"], "en-IN")

    def test_translation_error_is_safe(self):
        translator = SarvamTranslator(transport=lambda payload: (_ for _ in ()).throw(TimeoutError("timeout")), retries=0)
        result = translator.translate("भारत की राजधानी क्या है?")
        self.assertEqual(result["translated_text"], result["original_text"])
        self.assertIn("timeout", result["error"])

    def test_answer_language_switch_offline(self):
        adapter = AnswerLanguageAdapter(SarvamTranslator(transport=lambda _: (_ for _ in ()).throw(TimeoutError("offline")), retries=0))
        result = adapter.translate_answer("मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।", "en")
        self.assertEqual(result["answer_language"], "hi-IN")
        self.assertIn("ठीक हूँ", result["answer"])


if __name__ == "__main__": unittest.main()
