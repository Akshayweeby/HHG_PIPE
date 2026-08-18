<<<<<<< HEAD
# Prana — Multilingual Voice RAG
=======
# Prana — Voice RAG
>>>>>>> a5e1e696e22032afb1f408320409278e640d0de6

<p align="center">
  <strong>A multilingual, voice-enabled Retrieval-Augmented Generation system with grounded answers and safety-first guardrails.</strong>
</p>

<p align="center">
  <a href="https://hhg-pipe.vercel.app/"><img src="https://img.shields.io/badge/Live%20Demo-Open%20Website-00C7B7?logo=vercel&logoColor=white" alt="Live demo"></a>
  <a href="https://github.com/Akshayweeby/HHG_PIPE"><img src="https://img.shields.io/badge/Repository-GitHub-181717?logo=github" alt="GitHub repository"></a>
  <a href="https://github.com/Akshayweeby/HHG_PIPE/issues"><img src="https://img.shields.io/badge/Issues-Report%20a%20bug-e05d44?logo=github" alt="Report an issue"></a>
  <a href="https://github.com/Akshayweeby/HHG_PIPE/blob/main/README.md"><img src="https://img.shields.io/badge/Docs-README-5b5bd6?logo=readthedocs" alt="Documentation"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Multilingual-Hindi%20%7C%20English%20%7C%20Kannada%20%7C%20Marathi-7C3AED" alt="Multilingual support">
  <img src="https://img.shields.io/badge/Tests-Pytest-0A9EDC?logo=pytest&logoColor=white" alt="Pytest">
</p>

## Overview

Prana is a complete multilingual voice RAG pipeline that turns spoken questions into reliable, language-aware answers in English, Hindi, Kannada, and Marathi. It combines speech processing, multilingual retrieval, generation, citations, grounding checks, and defensive guardrails in one modular system.

Try the live application: [hhg-pipe.vercel.app](https://hhg-pipe.vercel.app/)

The pipeline is designed to answer only when the retrieved evidence supports the response. Unsupported, unsafe, off-topic, or low-confidence requests receive a clear fallback instead of a confident hallucination.

```text
Audio / question
      ↓
Speech-to-text + language detection
      ↓
Input guardrails
      ↓
Hybrid retrieval: dense + BM25 + RRF
      ↓
Answer generation with citations
      ↓
Multi-signal grounding validation
      ↓
Translated answer + optional voice response
```

## Key capabilities

- Voice-first interaction with server-side and browser speech fallbacks
- Hindi, English, Kannada, Marathi, and code-mixed query support
- Fixed, semantic, and hierarchical document chunking
- Dense retrieval with deterministic offline embeddings or injectable production embeddings
- Sparse BM25 retrieval with Reciprocal Rank Fusion (RRF)
- Guardrails for unsafe and off-topic inputs
- Citation validation and conservative grounding checks
- “I don’t know” responses when evidence is missing or insufficient
- Answer translation and text-to-speech output in the selected language
- Structured stage outputs, latency tracking, failure handling, and automated tests

## Technology stack

| Area | Technologies |
| --- | --- |
| Backend | Python, built-in `http.server`, REST-style JSON API |
| RAG | Custom retrieval pipeline, chunking, dense search, BM25, RRF |
| Embeddings | Deterministic hashing embedder offline; SentenceTransformer-compatible injection for production |
| Optional search | NumPy and FAISS-compatible dense index integration |
| Voice | Sarvam STT, Sarvam translation, Sarvam Bulbul TTS, Microsoft Edge neural voices |
| Frontend | HTML, CSS, vanilla JavaScript, responsive UI |
| Quality | Pytest, retrieval evaluation, Precision@k comparison |
| Data formats | JSON, JSONL, CSV, MSMARCO-XI-compatible records |

## Quick start

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For production retrieval, optionally install the packages used by your chosen embedding and indexing setup:

```powershell
pip install numpy faiss-cpu datasets sentence-transformers
```

### 2. Start the backend

```powershell
python server.py
```

The API starts at `http://127.0.0.1:8000`.

### 3. Start the frontend

```powershell
python -m http.server 5500 -d frontend
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500) in your browser.

## API examples

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Pipeline request:

```powershell
$body = @{
  audio = "भारत की राजधानी क्या है?"
  question_language = "hi"
  answer_language = "hi"
  speak_answer = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/pipeline `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Standalone retrieval:

```python
from retrieval.data import load_records
from retrieval.pipeline import RetrievalConfig, RetrievalSystem

records = load_records("msmarco_xi_validation.jsonl", limit=5000)
rag = RetrievalSystem(records, RetrievalConfig(strategy="semantic"))
results = rag.retrieve("भारत की राजधानी क्या है?", k=5)
```

## Configuration

Real Sarvam integrations can be enabled with environment variables such as:

```powershell
$env:SARVAM_API_SUBSCRIPTION_KEY = "your-key"
# or
$env:SARVAM_API_KEY = "your-key"
```

Without external service credentials, the project remains demo-friendly with deterministic retrieval, safe extractive generation, mocked service boundaries, and Microsoft Edge neural voice fallbacks where available.

## Testing and evaluation

```powershell
python -m pytest -q
python -m retrieval.demo
```

The test suite covers guardrails, grounding signals, citation validation, language handling, voice modules, retrieval strategies, failure paths, and end-to-end pipeline behavior.

## Project structure

```text
app/          Pipeline orchestration, guardrails, grounding, models, evaluation
frontend/     Main browser interface
retrieval/    Data loading, chunking, indexes, fusion, and retrieval evaluation
tests/        End-to-end and module-level tests
voice/        STT, generation, translation, language handling, and TTS
server.py     Lightweight HTTP server and JSON API entry point
```

## Roadmap

- Connect production embedding and FAISS deployments
- Add persistent document ingestion and indexing
- Expand evaluation datasets and retrieval metrics
- Add authentication, rate limiting, and deployment configuration
- Publish a hosted demo for multilingual voice queries

## Collaborators

Built with care by:

<table align="center">
    <thead>
      <tr>
        <th>Collaborator</th>
        <th>GitHub</th>
        <th>Focus</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Akshayweeby</td>
        <td><a href="https://github.com/Akshayweeby">@Akshayweeby</a></td>
        <td>Pipeline, guardrails, and frontend</td>
      </tr>
      <tr>
        <td>Shrak24</td>
        <td><a href="https://github.com/Shrak24">@Shrak24</a></td>
        <td>Multilingual retrieval</td>
      </tr>
      <tr>
        <td>RaiderX547</td>
        <td><a href="https://github.com/RaiderX547">@RaiderX547</a></td>
        <td>Voice and answer generation</td>
      </tr>
    </tbody>
</table>

<p align="center">If you find this project useful, consider giving it a ⭐ on GitHub.</p>
