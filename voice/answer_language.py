"""Keep the answer in the same language as the user's question."""
from __future__ import annotations

from .translation import SarvamTranslator


class AnswerLanguageAdapter:
    TARGETS = {"en": "en-IN", "hi": "hi-IN", "kn": "kn-IN", "mr": "mr-IN"}
    OFFLINE = {
        ("en-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "I am fine and ready to help you.",
        ("hi-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।",
        ("en-IN", "मैं आपका कृत्रिम बुद्धिमत्ता सहायक हूँ।"): "I am your AI assistant.",
        ("hi-IN", "मैं आपका कृत्रिम बुद्धिमत्ता सहायक हूँ।"): "मैं आपका कृत्रिम बुद्धिमत्ता सहायक हूँ।",
        ("en-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "The RAG pipeline retrieves relevant documents and generates a grounded answer from their context.",
        ("hi-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "आरएजी पाइपलाइन संबंधित दस्तावेज़ों को खोजकर उनके संदर्भ के आधार पर उत्तर तैयार करती है।",
<<<<<<< HEAD
        ("kn-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ ಮತ್ತು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧನಿದ್ದೇನೆ.",
        ("mr-IN", "मैं ठीक हूँ और आपकी मदद करने के लिए तैयार हूँ।"): "मी ठीक आहे आणि तुम्हाला मदत करण्यासाठी तयार आहे.",
        ("kn-IN", "मैं आपका कृत्रिम बुद्धिमत्ता सहायक हूँ।"): "ನಾನು ನಿಮ್ಮ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆಯ ಸಹಾಯಕನಾಗಿದ್ದೇನೆ.",
        ("mr-IN", "मैं आपका कृत्रिम बुद्धिमत्ता सहायक हूँ।"): "मी तुमचा कृत्रिम बुद्धिमत्ता सहाय्यक आहे.",
        ("kn-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "RAG ಪೈಪ್‌ಲೈನ್ ಸಂಬಂಧಿತ ದಾಖಲೆಗಳನ್ನು ಹುಡುಕಿ, ಅವುಗಳ ಸಂದರ್ಭದ ಆಧಾರದ ಮೇಲೆ ಉತ್ತರವನ್ನು ತಯಾರಿಸುತ್ತದೆ.",
        ("mr-IN", "RAG pipeline relevant documents retrieve करके उनके context पर grounded उत्तर generate करता है।"): "RAG पाइपलाइन संबंधित कागदपत्रे शोधून त्यांच्या संदर्भावर आधारित उत्तर तयार करते.",
        ("en-IN", "मुझे इस उत्तर के लिए पर्याप्त प्रमाण नहीं मिला।"): "I could not find enough evidence for this answer.",
        ("kn-IN", "मुझे इस उत्तर के लिए पर्याप्त प्रमाण नहीं मिला।"): "ಈ ಉತ್ತರಕ್ಕೆ ಸಾಕಷ್ಟು ಪುರಾವೆಗಳು ದೊರಕಲಿಲ್ಲ.",
        ("mr-IN", "मुझे इस उत्तर के लिए पर्याप्त प्रमाण नहीं मिला।"): "या उत्तरासाठी पुरेसा पुरावा मिळाला नाही.",
        ("en-IN", "यह सवाल इस डेमो के RAG विषय से बाहर है।"): "This question is outside this demo's supported topic.",
        ("kn-IN", "यह सवाल इस डेमो के RAG विषय से बाहर है।"): "ಈ ಪ್ರಶ್ನೆಯು ಈ ಡೆಮೊದ ಬೆಂಬಲಿತ ವಿಷಯದ ಹೊರಗಿದೆ.",
        ("mr-IN", "यह सवाल इस डेमो के RAG विषय से बाहर है।"): "हा प्रश्न या डेमोच्या समर्थित विषयाबाहेर आहे.",
        ("en-IN", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।"): "This input appears to be an unsafe request.",
        ("kn-IN", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।"): "ಈ ಇನ್‌ಪುಟ್ ಅಸುರಕ್ಷಿತ ವಿನಂತಿಯಂತೆ ಕಾಣುತ್ತದೆ.",
        ("mr-IN", "यह इनपुट असुरक्षित अनुरोध जैसा दिखता है।"): "हा इनपुट असुरक्षित विनंतीसारखा दिसतो.",
        ("en-IN", "प्रमाण उपलब्ध नहीं है। मैं इस प्रश्न का उत्तर नहीं दे सकता।"): "Evidence is unavailable. I cannot answer this question.",
        ("kn-IN", "प्रमाण उपलब्ध नहीं है। मैं इस प्रश्न का उत्तर नहीं दे सकता।"): "ಪುರಾವೆಗಳು ಲಭ್ಯವಿಲ್ಲ. ಈ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        ("mr-IN", "प्रमाण उपलब्ध नहीं है। मैं इस प्रश्न का उत्तर नहीं दे सकता।"): "पुरावा उपलब्ध नाही. मी या प्रश्नाचे उत्तर देऊ शकत नाही.",
        ("kn-IN", "grounded by all configured signals"): "ಎಲ್ಲಾ ಪರಿಶೀಲನಾ ಸೂಚನೆಗಳ ಆಧಾರದ ಮೇಲೆ ಉತ್ತರವನ್ನು ದೃಢೀಕರಿಸಲಾಗಿದೆ.",
        ("mr-IN", "grounded by all configured signals"): "सर्व पडताळणी संकेतांच्या आधारे उत्तराची पुष्टी झाली आहे.",
        ("kn-IN", "मैं आपका AI assistant हूँ।"): "ನಾನು ನಿಮ್ಮ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಸಹಾಯಕ.",
        ("mr-IN", "मैं आपका AI assistant हूँ।"): "मी तुमचा कृत्रिम बुद्धिमत्ता सहाय्यक आहे.",
=======
        ("hi-IN", "A flower is the reproductive part of a flowering plant and helps the plant produce seeds."): "फूल पुष्पीय पौधे का प्रजनन अंग होता है और पौधे को बीज बनाने में मदद करता है।",
        ("en-IN", "A flower is the reproductive part of a flowering plant and helps the plant produce seeds."): "A flower is the reproductive part of a flowering plant and helps the plant produce seeds.",
>>>>>>> 53b83f651084540b296c86346f5e2b41b6feb68f
    }

    def __init__(self, translator: SarvamTranslator | None = None):
        self.translator = translator or SarvamTranslator()

    @classmethod
    def target_for(cls, question_language: str) -> str:
        key = str(question_language or "en").lower().split("-")[0]
        return cls.TARGETS.get(key, "hi-IN")

    def translate_answer(self, answer: str, question_language: str) -> dict[str, str | None]:
        target = self.target_for(question_language)
        # The current offline generator already produces Hindi. Returning it
        # directly avoids turning a valid Hindi answer into a translation
        # service error when the optional translator is not configured.
        if target == "hi-IN":
            return {"answer": answer, "answer_language": target, "translation_error": None}
        result = self.translator.translate(answer, source_language_code="auto", target_language_code=target, mode="formal")
        if not result.get("error") and result.get("translated_text"):
            return {"answer": str(result["translated_text"]), "answer_language": target, "translation_error": None}
        fallback = self.OFFLINE.get((target, answer))
        if fallback:
            return {"answer": fallback, "answer_language": target, "translation_error": result.get("error")}
        unavailable = "अनुवाद सेवा उपलब्ध नहीं है।" if target == "hi-IN" else "Translation service is unavailable."
        return {"answer": unavailable, "answer_language": target, "translation_error": result.get("error")}
