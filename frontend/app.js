const state = { questionLanguage: "en", answerLanguage: "en", lastAnswer: "" };
const $ = (id) => document.getElementById(id);
const API_URL = window.location.port === "8000"
  ? "/api/pipeline"
  : "http://127.0.0.1:8000/api/pipeline";
const LANGUAGE_LABELS = { en: "English", hi: "हिंदी", kn: "ಕನ್ನಡ", mr: "मराठी" };
const SPEECH_CODES = { en: "en-IN", hi: "hi-IN", kn: "kn-IN", mr: "mr-IN" };
const QUESTION_COPY = {
  en: { hint: "Try: What is the RAG pipeline?", placeholder: "Ask anything about the available knowledge base..." },
  hi: { hint: "उदाहरण: भारत की राजधानी क्या है?", placeholder: "उपलब्ध जानकारी के बारे में कुछ भी पूछें..." },
  kn: { hint: "ಉದಾಹರಣೆ: RAG ಪೈಪ್‌ಲೈನ್ ಎಂದರೇನು?", placeholder: "ಲಭ್ಯವಿರುವ ಮಾಹಿತಿಯ ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ..." },
  mr: { hint: "उदाहरण: RAG पाइपलाइन म्हणजे काय?", placeholder: "उपलब्ध माहितीबद्दल काहीही विचारा..." },
};

function languageOptions(select) {
  Object.entries(LANGUAGE_LABELS).forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
}

// Expose all four languages even when an older cached index.html is open.
const questionOptions = document.querySelector(".language-options");
["kn", "mr"].forEach((language) => {
  if (!questionOptions?.querySelector(`[data-lang="${language}"]`)) {
    const button = document.createElement("button");
    button.className = "lang";
    button.dataset.lang = language;
    button.textContent = LANGUAGE_LABELS[language];
    questionOptions?.appendChild(button);
  }
});

// The answer language is independent from the question language.
const answerControl = document.createElement("label");
answerControl.className = "answer-language-control";
answerControl.innerHTML = "Answer language <select id=\"answer-language-select\"></select>";
document.querySelector(".field-head")?.appendChild(answerControl);
languageOptions($("answer-language-select"));
$("answer-language-select").value = state.answerLanguage;
$("answer-language-select").addEventListener("change", (event) => {
  state.answerLanguage = event.target.value;
});

// Voice input and read-aloud use the browser speech APIs, so they work without
// an API key and feel like the listen button in a translation app.
const voiceControls = document.createElement("div");
voiceControls.className = "voice-controls";
voiceControls.innerHTML = `
  <button id="voice-input" type="button">🎙 Ask by voice</button>
  <button id="read-answer" type="button" disabled>🔊 Read answer</button>
  <span id="voice-status">Type or use your microphone</span>`;
$("question")?.insertAdjacentElement("afterend", voiceControls);

function setQuestionLanguage(language) {
  state.questionLanguage = language;
  document.querySelectorAll(".lang").forEach((button) =>
    button.classList.toggle("active", button.dataset.lang === language));
  $("input-hint").textContent = QUESTION_COPY[language].hint;
  $("question").placeholder = QUESTION_COPY[language].placeholder;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[char]));
}

function setAnswer(data) {
  const panel = $("answer-panel");
  panel.classList.remove("empty");
  const answer = data.answer || (data.state === "NO_EVIDENCE"
    ? "I don't know based on the available context."
    : data.state === "REPEAT_LOW_CONFIDENCE" ? "Please repeat your question." : "I don't know.");
  state.lastAnswer = answer;
  $("read-answer").disabled = !answer;
  const citations = (data.citations || []).map((citation) =>
    `<span class="tag">↗ ${escapeHtml(citation)}</span>`).join("");
  const language = data.answer_language
    ? `<span class="tag">${escapeHtml(data.answer_language)}</span>` : "";
  panel.innerHTML = `
    <div class="field-head"><span class="eyebrow">Final response</span>
      <span class="tag">${escapeHtml(data.state || "ANSWER")}</span></div>
    <h3>${escapeHtml(answer)}</h3>
    <p>${escapeHtml(data.reason || "Grounded against the available context.")}</p>
    <div>${citations} ${language}</div>`;
}

async function ask() {
  const question = $("question").value.trim();
  if (!question) {
    $("question").focus();
    return;
  }
  const button = $("ask");
  button.disabled = true;
  button.textContent = "Thinking …";
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audio: question,
        question_language: state.questionLanguage,
        answer_language: state.answerLanguage,
        speak_answer: false,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The backend request failed.");
    setAnswer(data);
  } catch (error) {
    setAnswer({ state: "ERROR", reason: error.message });
  } finally {
    button.disabled = false;
    button.textContent = "Run retrieval →";
  }
}

function startVoiceInput() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    $("voice-status").textContent = "Voice input is not supported in this browser.";
    return;
  }
  const recognition = new Recognition();
  recognition.lang = SPEECH_CODES[state.questionLanguage];
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  $("voice-status").textContent = "Listening… speak now";
  recognition.onresult = (event) => {
    $("question").value = event.results[0][0].transcript;
    $("voice-status").textContent = "Voice captured. Press Run retrieval.";
  };
  recognition.onerror = () => { $("voice-status").textContent = "Could not capture voice. Try again."; };
  recognition.onend = () => {
    if ($("voice-status").textContent === "Listening… speak now") $("voice-status").textContent = "Ready";
  };
  recognition.start();
}

function readAnswer() {
  const synth = window.speechSynthesis;
  if (!state.lastAnswer) return;
  if (!synth || !window.SpeechSynthesisUtterance) {
    $("voice-status").textContent = "Read aloud is not supported in this browser.";
    return;
  }
  synth.cancel();
  synth.resume();
  const speak = () => {
    const utterance = new SpeechSynthesisUtterance(state.lastAnswer);
    utterance.lang = SPEECH_CODES[state.answerLanguage];
    utterance.rate = 0.92;
    const voices = synth.getVoices();
    const targetPrefix = SPEECH_CODES[state.answerLanguage].slice(0, 2).toLowerCase();
    const preferred = voices.find((voice) => voice.lang?.toLowerCase().startsWith(targetPrefix));
    const fallback = voices.find((voice) => voice.lang?.toLowerCase().startsWith("hi"))
      || voices.find((voice) => voice.lang?.toLowerCase().startsWith("en"))
      || voices[0];
    if (preferred) {
      utterance.voice = preferred;
    } else if (fallback) {
      // Many systems do not ship kn-IN/mr-IN voices. Use an installed voice
      // so the answer remains audible rather than failing silently.
      utterance.voice = fallback;
      utterance.lang = fallback.lang || "en-IN";
    }
    utterance.onstart = () => {
      $("voice-status").textContent = preferred
        ? `Reading in ${LANGUAGE_LABELS[state.answerLanguage]}…`
        : `Reading with an available voice…`;
    };
    utterance.onend = () => { $("voice-status").textContent = "Ready"; };
    utterance.onerror = () => { $("voice-status").textContent = "Could not read the answer aloud."; };
    synth.speak(utterance);
  };
  // Chrome loads its voice list asynchronously on the first request.
  if (synth.getVoices().length) speak();
  else synth.addEventListener("voiceschanged", speak, { once: true });
}

document.querySelectorAll(".lang").forEach((button) =>
  button.addEventListener("click", () => setQuestionLanguage(button.dataset.lang)));
document.querySelectorAll(".quick-asks button").forEach((button) =>
  button.addEventListener("click", () => { $("question").value = button.dataset.question; ask(); }));
$("ask").addEventListener("click", ask);
$("voice-input").addEventListener("click", startVoiceInput);
$("read-answer").addEventListener("click", readAnswer);
$("question").addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") ask();
});
setQuestionLanguage("en");
