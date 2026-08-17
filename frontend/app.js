const state = { language: "en" };
const $ = (id) => document.getElementById(id);
const API_URL = window.location.port === "8000"
  ? "/api/pipeline"
  : "http://127.0.0.1:8000/api/pipeline";

function setLanguage(language) {
  state.language = language;
  document.querySelectorAll(".lang").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === language);
  });
  $("answer-language").textContent = language === "en" ? "Answer: Hindi" : "Answer: English";
  $("input-hint").textContent = language === "en"
    ? "Try: What is the RAG pipeline?"
    : "Try: भारत की राजधानी क्या है?";
  $("question").placeholder = language === "en"
    ? "Ask anything about the available knowledge base..."
    : "उपलब्ध जानकारी के बारे में कुछ भी पूछें...";
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
        question_language: state.language,
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

document.querySelectorAll(".lang").forEach((button) =>
  button.addEventListener("click", () => setLanguage(button.dataset.lang)));
document.querySelectorAll(".quick-asks button").forEach((button) =>
  button.addEventListener("click", () => {
    $("question").value = button.dataset.question;
    ask();
  }));
$("ask").addEventListener("click", ask);
$("question").addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") ask();
});
setLanguage("en");
