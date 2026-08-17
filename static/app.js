const $ = id => document.getElementById(id);
const query = $('query');
const language = $('question-language');
let latestAnswer = '';
let latestAudio = null;
const answerLabels = { en: 'English', hi: 'हिंदी', kn: 'ಕನ್ನಡ', mr: 'मराठी' };
const locales = { en: 'en-IN', hi: 'hi-IN', kn: 'kn-IN', mr: 'mr-IN' };
const noAnswerText = { 'en-IN': 'I don’t know', 'hi-IN': 'मुझे नहीं पता', 'kn-IN': 'ನನಗೆ ಗೊತ್ತಿಲ್ಲ', 'mr-IN': 'मला माहीत नाही' };
let answerLocale = locales.en;
let availableVoices = [];

function refreshVoices() {
  if ('speechSynthesis' in window) availableVoices = window.speechSynthesis.getVoices();
}
function matchingVoice(locale) {
  const wanted = locale.toLowerCase();
  return availableVoices.find(v => v.lang.toLowerCase() === wanted) || availableVoices.find(v => v.lang.toLowerCase().startsWith(wanted.slice(0, 2))) || null;
}

function updateLanguageHint() {
  const key = language.value;
  $('answer-language').textContent = `Answer will be in ${answerLabels[key]}`;
  query.placeholder = { hi: 'आरएजी पाइपलाइन क्या है?', kn: 'RAG ಪೈಪ್‌ಲೈನ್ ಎಂದರೇನು?', mr: 'RAG पाइपलाइन म्हणजे काय?' }[key] || 'What is the RAG pipeline?';
}
function setLoading(on) { $('loading').classList.toggle('hidden', !on); $('result').classList.toggle('hidden', on); }
async function run(audio = query.value, scenario = null) {
  setLoading(true); $('recording').textContent = '';
  try { const res = await fetch('/api/pipeline', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ audio, demo_scenario: scenario, question_language: language.value, speak_answer: true }) }); render(await res.json()); }
  catch (e) { render({ state: 'ERROR', reason: e.message, timings: [] }); }
  finally { setLoading(false); }
}
function render(d) {
  $('state').textContent = d.state; $('state').style.color = d.state === 'ALLOW' ? 'var(--green)' : 'var(--red)';
  answerLocale = d.answer_language || locales[language.value] || locales.en;
  latestAnswer = d.answer || (d.state === 'REPEAT_LOW_CONFIDENCE' ? ({ 'hi-IN': 'कृपया दोबारा बोलें', 'kn-IN': 'ದಯವಿಟ್ಟು ಮತ್ತೆ ಮಾತನಾಡಿ', 'mr-IN': 'कृपया पुन्हा बोला', 'en-IN': 'Please repeat' }[answerLocale] || 'Please repeat') : (noAnswerText[answerLocale] || 'I don’t know')); $('answer').textContent = latestAnswer; $('reason').textContent = d.reason || '';
  $('citations').innerHTML = (d.citations || []).map(c => `<span class="citation">↳ ${c}</span>`).join('');
  latestAudio = d.answer_audio?.audio_base64 ? `data:${d.answer_audio.mime_type};base64,${d.answer_audio.audio_base64}` : null;
  refreshVoices();
  $('speech-status').textContent = latestAudio ? 'Audio ready' : (matchingVoice(answerLocale) ? 'Browser voice ready' : `No ${answerLocale} voice available; configure server TTS`);
  const g = d.grounding; $('grounding-status').textContent = g ? 'OBSERVED' : '—'; $('similarity').textContent = g ? g.embedding_similarity.toFixed(2) : '—'; $('critique').textContent = g ? (g.llm_self_critique ? 'PASS' : 'FAIL') : '—'; $('citation-valid').textContent = g ? (g.citation_validity ? 'PASS' : 'FAIL') : '—';
  const ts = d.timings || [], total = ts.find(t => t.stage === 'total'); $('total-latency').textContent = total ? `${total.duration_ms} ms` : ''; $('timings').innerHTML = ts.filter(t => t.stage !== 'total').map(t => `<div class="timing"><span>${t.stage}</span><b>${t.duration_ms} ms</b></div>`).join('');
}
function speakAnswer() {
  if (!latestAnswer) return;
  if (latestAudio) { new Audio(latestAudio).play().catch(() => { $('speech-status').textContent = 'Press Speak answer again to allow playback.'; }); return; }
  if (!('speechSynthesis' in window)) { $('speech-status').textContent = 'Speech playback is unavailable in this browser.'; return; }
  refreshVoices(); const voice = matchingVoice(answerLocale);
  if (!voice) { $('speech-status').textContent = `No ${answerLocale} voice is installed. Configure SARVAM_API_SUBSCRIPTION_KEY for multilingual audio.`; return; }
  window.speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(latestAnswer); utterance.lang = answerLocale; utterance.voice = voice; window.speechSynthesis.speak(utterance); $('speech-status').textContent = `Speaking the complete answer in ${answerLocale}`;
}
document.querySelectorAll('.chips button').forEach(b => b.onclick = () => { query.value = b.dataset.value || ''; run(query.value, b.dataset.scenario || null); }); $('run').onclick = () => run(); $('speak-answer').onclick = speakAnswer; language.onchange = updateLanguageHint; updateLanguageHint();
$('mic').onclick = () => { if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) { $('recording').textContent = 'Microphone speech recognition is unavailable; type a demo question instead.'; return; } const R = window.SpeechRecognition || window.webkitSpeechRecognition, r = new R(); r.lang = locales[language.value]; $('recording').textContent = 'Listening…'; r.onresult = e => { query.value = e.results[0][0].transcript; $('recording').textContent = 'Captured microphone input.'; }; r.onerror = () => { $('recording').textContent = 'Microphone capture failed. You can type a question.'; }; r.start(); };
if ('speechSynthesis' in window) { refreshVoices(); window.speechSynthesis.onvoiceschanged = refreshVoices; }
