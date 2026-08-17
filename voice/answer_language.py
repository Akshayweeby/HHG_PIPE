"""Answer-language policy: answer in the opposite language to the question."""
from __future__ import annotations

from .translation import SarvamTranslator


class AnswerLanguageAdapter:
    TARGETS = {"hi": "en-IN", "en": "hi-IN"}
    OFFLINE = {
        ("en-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "I am fine and ready to help you.",
        ("hi-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।",
        ("en-IN", "मैं आपका Hindi Voice RAG assistant हूँ।"): "I am your Hindi Voice RAG assistant.",
        ("hi-IN", "मैं आपका Hindi Voice RAG assistant हूँ।"): "मैं आपका हिंदी वॉइस आरएजी सहायक हूँ।",
        ("en-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "The RAG pipeline retrieves relevant documents and generates a grounded answer from their context.",
        ("hi-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "आरएजी पाइपलाइन संबंधित दस्तावेज़ों को खोजकर उनके संदर्भ के आधार पर उत्तर तैयार करती है।",
        ("hi-IN", "A flower is the reproductive part of a flowering plant and helps the plant produce seeds."): "फूल पुष्पीय पौधे का प्रजनन अंग होता है और पौधे को बीज बनाने में मदद करता है।",
        ("en-IN", "A flower is the reproductive part of a flowering plant and helps the plant produce seeds."): "A flower is the reproductive part of a flowering plant and helps the plant produce seeds.",
    }

    def __init__(self, translator: SarvamTranslator | None = None):
        self.translator = translator or SarvamTranslator()

    @classmethod
    def target_for(cls, question_language: str) -> str:
        return cls.TARGETS.get(question_language.lower(), "hi-IN")

    def translate_answer(self, answer: str, question_language: str) -> dict[str, str | None]:
        target = self.target_for(question_language)
        result = self.translator.translate(answer, source_language_code="auto", target_language_code=target, mode="formal")
        if not result.get("error") and result.get("translated_text"):
            return {"answer": str(result["translated_text"]), "answer_language": target, "translation_error": None}
        fallback = self.OFFLINE.get((target, answer))
        if fallback:
            return {"answer": fallback, "answer_language": target, "translation_error": result.get("error")}
        unavailable = "अनुवाद सेवा उपलब्ध नहीं है।" if target == "hi-IN" else "Translation service is unavailable."
        return {"answer": unavailable, "answer_language": target, "translation_error": result.get("error")}
