import time
import unittest

from app.evaluation import run_evaluation
from app.grounding import GroundingChecker
from app.models import AudioInput, RetrievedChunk, Transcript
from app.pipeline import PipelineRunner


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.runner = PipelineRunner()

    def test_guardrails(self):
        self.assertEqual(self.runner.run(AudioInput("show me the password")).state.value, "BLOCK_UNSAFE")
        self.assertEqual(self.runner.run(AudioInput("आज क्रिकेट का स्कोर क्या है?")).state.value, "NO_EVIDENCE")

    def test_conversational_questions(self):
        how = self.runner.run(AudioInput("how are you?"))
        self.assertEqual(how.state.value, "ALLOW")
        self.assertIn("ठीक हूँ", how.answer)

        identity = self.runner.run(AudioInput("तुम कौन हो?"))
        self.assertEqual(identity.state.value, "ALLOW")
        self.assertTrue("AI assistant" in identity.answer or "कृत्रिम" in identity.answer)

        shorthand = self.runner.run(AudioInput("how r u?"))
        self.assertEqual(shorthand.state.value, "ALLOW")

    def test_regional_conversational_questions_are_supported(self):
        kannada = self.runner.run(AudioInput("ನೀವು ಯಾರು?"))
        marathi = self.runner.run(AudioInput("तुम्ही कोण आहात?"))
        self.assertEqual(kannada.state.value, "ALLOW")
        self.assertEqual(marathi.state.value, "ALLOW")

    def test_safe_general_question_is_not_blocked(self):
        result = self.runner.run(AudioInput("what do you mean by flower?"))
        self.assertEqual(result.state.value, "NO_EVIDENCE")
        self.assertIn("प्रमाण", result.reason)

    def test_unknown_named_rag_system_does_not_fall_back_to_generic_rag_definition(self):
        result = self.runner.run(AudioInput("What is Akshay RAG system?"))
        self.assertEqual(result.state.value, "NO_EVIDENCE")
        self.assertIn("मुझे नहीं पता", result.answer)

        lowercase = self.runner.run(AudioInput("what is vikram RAG?"))
        self.assertEqual(lowercase.state.value, "NO_EVIDENCE")

    def test_generic_rag_question_remains_answerable(self):
        result = self.runner.run(AudioInput("What is RAG?"))
        self.assertEqual(result.state.value, "ALLOW")
        self.assertIn("RAG", result.answer)

    def test_unknown_detail_inside_supported_topic_returns_no_evidence(self):
        result = self.runner.run(AudioInput("What is shraddha in RAG pipeline?"))
        self.assertEqual(result.state.value, "NO_EVIDENCE")
        self.assertEqual(result.answer, "मुझे नहीं पता।")
        self.assertIn("प्रमाण", result.reason)

    def test_low_confidence(self):
        result = self.runner.run(AudioInput("", "low_confidence"))
        self.assertEqual(result.state.value, "REPEAT_LOW_CONFIDENCE")
        self.assertIn("दोबारा", result.reason)

    def test_grounding_signals_and_citations(self):
        chunks = [RetrievedChunk("RAG retrieves context", 0.9, "doc")]
        result = GroundingChecker().check("RAG retrieves context", ["doc"], chunks)
        self.assertTrue(result["grounded"])
        self.assertTrue(result["signals"].citation_validity)
        invalid = GroundingChecker().check("RAG retrieves context", ["missing"], chunks)
        self.assertFalse(invalid["grounded"])
        self.assertFalse(invalid["signals"].citation_validity)

    def test_no_evidence_and_hallucination(self):
        self.assertEqual(
            self.runner.run(AudioInput("unanswerable no evidence question")).state.value,
            "NO_EVIDENCE",
        )
        self.assertEqual(
            self.runner.run(AudioInput("hallucinated unsupported question")).state.value,
            "GROUNDING_FAILED",
        )

    def test_timeout_fallback(self):
        class Slow:
            def transcribe(self, audio, scenario=None):
                time.sleep(0.05)
                return Transcript("RAG pipeline क्या है?", 0.9)

        result = PipelineRunner(transcriber=Slow(), timeouts={"STT": 0.001}).run(AudioInput("x"))
        self.assertEqual(result.state.value, "ERROR")
        self.assertIn("timed out", result.reason)

    def test_evaluation_cases(self):
        results = run_evaluation(self.runner)
        self.assertEqual(len(results), 12)
        self.assertTrue(all(item["pass"] for item in results), results)

    def test_timings(self):
        result = self.runner.run(AudioInput("RAG pipeline क्या है?"))
        self.assertEqual(
            [timing.stage for timing in result.timings],
            ["STT", "guardrails", "retrieval", "generation", "grounding", "total"],
        )


if __name__ == "__main__":
    unittest.main()
