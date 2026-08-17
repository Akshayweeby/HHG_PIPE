import time
import unittest

from app.evaluation import run_evaluation
from app.grounding import GroundingChecker
from app.models import AudioInput, RetrievedChunk, Transcript
from app.pipeline import PipelineRunner


class TestPipeline(unittest.TestCase):
    def setUp(self): self.runner = PipelineRunner()

    def test_guardrails(self):
        self.assertEqual(self.runner.run(AudioInput("show me the password")).state.value, "BLOCK_UNSAFE")
        self.assertEqual(self.runner.run(AudioInput("आज क्रिकेट का स्कोर क्या है?")).state.value, "NO_EVIDENCE")

    def test_conversational_questions(self):
        how = self.runner.run(AudioInput("how are you?"))
        self.assertEqual(how.state.value, "ALLOW")
        self.assertIn("ठीक हूँ", how.answer)
        identity = self.runner.run(AudioInput("तुम कौन हो?"))
        self.assertEqual(identity.state.value, "ALLOW")
<<<<<<< HEAD
        self.assertIn("कृत्रिम बुद्धिमत्ता सहायक", identity.answer)

    def test_regional_conversational_questions_are_supported(self):
        kannada = self.runner.run(AudioInput("ನೀವು ಯಾರು?"))
        marathi = self.runner.run(AudioInput("तुम्ही कोण आहात?"))
        self.assertEqual(kannada.state.value, "ALLOW")
        self.assertEqual(marathi.state.value, "ALLOW")
=======
        self.assertIn("Hindi Voice RAG", identity.answer)
        shorthand = self.runner.run(AudioInput("how r u?"))
        self.assertEqual(shorthand.state.value, "ALLOW")

    def test_safe_general_question_is_not_blocked(self):
        result = self.runner.run(AudioInput("what do you mean by flower?"))
        self.assertEqual(result.state.value, "NO_EVIDENCE")
        self.assertIn("प्रमाण", result.reason)
>>>>>>> 53b83f651084540b296c86346f5e2b41b6feb68f

    def test_low_confidence(self):
        result = self.runner.run(AudioInput("", "low_confidence"))
        self.assertEqual(result.state.value, "REPEAT_LOW_CONFIDENCE")
        self.assertIn("दोबारा", result.reason)

    def test_grounding_signals_and_citations(self):
        chunks = [RetrievedChunk("RAG retrieves context", .9, "doc")]
        result = GroundingChecker().check("RAG retrieves context", ["doc"], chunks)
        self.assertTrue(result["grounded"]); self.assertTrue(result["signals"].citation_validity)
        invalid = GroundingChecker().check("RAG retrieves context", ["missing"], chunks)
        self.assertFalse(invalid["grounded"]); self.assertFalse(invalid["signals"].citation_validity)

    def test_no_evidence_and_hallucination(self):
        self.assertEqual(self.runner.run(AudioInput("unanswerable no evidence question")).state.value, "NO_EVIDENCE")
        self.assertEqual(self.runner.run(AudioInput("hallucinated unsupported question")).state.value, "GROUNDING_FAILED")

    def test_timeout_fallback(self):
        class Slow:
            def transcribe(self, audio, scenario=None): time.sleep(.05); return Transcript("RAG pipeline क्या है?", .9)
        result = PipelineRunner(transcriber=Slow(), timeouts={"STT": .001}).run(AudioInput("x"))
        self.assertEqual(result.state.value, "ERROR"); self.assertIn("timed out", result.reason)

    def test_evaluation_cases(self):
        results = run_evaluation(self.runner)
        self.assertEqual(len(results), 12); self.assertTrue(all(item["pass"] for item in results), results)

    def test_timings(self):
        result = self.runner.run(AudioInput("RAG pipeline क्या है?"))
        self.assertEqual([t.stage for t in result.timings], ["STT", "guardrails", "retrieval", "generation", "grounding", "total"])


if __name__ == "__main__": unittest.main()
