# TruthGuard AI — Evidence-First Misinformation Analyzer

An **evidence-first** misinformation detection and verification engine. Unlike static LLM-based fact-checkers that rely on parametric memory (which suffers from hallucinations, temporal decay, and ungrounded assertions), TruthGuard AI executes an end-to-end multi-stage pipeline: real-time web retrieval, source authority classification, content extraction, semantic relevance ranking, quality gate filtering, grounded LLM verification, and strict citation provenance validation.

---

## 📋 Overview

### The Problem
Generative AI models and LLMs often answer factual queries using static weights trained on historical data. When asked to evaluate modern news or complex claims, LLMs frequently hallucinate facts, confuse topically related articles with proof, or assert outdated information with high confidence.

### The Solution
TruthGuard AI enforces strict **evidence grounding**. Rather than letting an LLM generate assertions from memory:
1. The system retrieves real-time web evidence and published fact-checks.
2. It categorizes domains into explicit authority tiers (Primary, Secondary, Low-Confidence).
3. It ranks extracted passages using `BAAI/bge-m3` semantic embeddings.
4. It filters low-quality or off-topic snippets through a strict Evidence Quality Gate.
5. It instructs the LLM (`meta-llama/Llama-3.3-70B-Instruct`) to evaluate logical entailment *exclusively* against retrieved passages.
6. It validates model citation IDs against retrieved sources to eliminate hallucinated references.

---

## 🎯 Key Features

- **Multi-Format Input Support**: Analyzes plain-text statements, public webpage URLs, URL + contextual questions, and uploaded image flyers or screenshots.
- **Browser-Native Speech-to-Text (STT)**: Integrated microphone input allowing users to speak claims directly into the analyzer.
- **Real-Time Web Retrieval**: Searches live web sources via DuckDuckGo Search (`ddgs`) with optional Google Fact Check Tools API lookup.
- **Authoritative Source Tiering**: Classifies domains into Primary (government/academic), Secondary (reputable news/fact-checkers), and Low-Confidence (social media/blogs) tiers.
- **BGE-M3 Semantic Ranking**: Scores passage relevance using vector embeddings, clearly separating topical relevance from truth probability.
- **Evidence Quality Gate**: Filters out malformed URLs, short snippets, duplicates, and low-relevance passages before LLM verification.
- **Grounded LLM Verification & Heuristic Fallback**: Evaluates claim stance using Llama 3.3 70B, with a degraded heuristic fallback mode if API tokens are unconfigured or rate-limited.
- **Strict Provenance Validation**: Rejects unmappable or hallucinated model evidence references.
- **Transparent Output**: Returns non-binary verdicts, confidence scores, semantic relevance percentages, direct answers, evidence passages, source lists, and explicit limitations.

---

## ⚙️ System Architecture

```
                       [User Input: Text Claim / URL / Image / Speech]
                                             │
                                             ▼
                                 [Input Mode & Intent Detection]
                                             │
    ┌────────────────────────────────────────┼────────────────────────────────────────┐
    ▼                                        ▼                                        ▼
[Text Claim Mode]                  [URL Verification Mode]                    [Image OCR Mode]
    │                                        │                                        │
    ▼                                        ▼                                        ▼
[Claim Parsing & Querying]        [Safe Page Fetch & Context]             [RapidOCR Text Extraction]
    │                                        │                                        │
    ▼                                        ▼                                        ▼
[Real Web Search]            [Independent Evidence Search]         [Claim Proposition Extraction]
(DDGS + Google Fact Check)                   │                                        │
    │                                        │                                        │
    └────────────────────────────────────────┼────────────────────────────────────────┘
                                             │
                                             ▼
                                  [Source Quality Tiering]
                          (Primary / Secondary / Low-Confidence)
                                             │
                                             ▼
                                [Content Passage Extraction]
                                (HTML Cleaning & Chunking)
                                             │
                                             ▼
                                [BGE-M3 Semantic Ranking]
                        (SentenceTransformers / HF API / Lexical)
                                             │
                                             ▼
                                 [Evidence Quality Gate]
                     (URL Validity, Length, Dedup, Tier Thresholds)
                                             │
                                             ▼
                             [Grounded LLM Verification]
                 (Llama 3.3 70B via HF Inference / Heuristic Fallback)
                                             │
                                             ▼
                              [Provenance & Citation Validation]
                              (ID Matching & Stance Consistency)
                                             │
                                             ▼
                              [Verdict + Explanation + Evidence]
                                             │
                                             ▼
                                 [Frontend Web Dashboard]
```

---

## 📥 Supported Input Modes

1. **Text Claim Mode**:
   - Accepts plain-text statements (e.g., *"NASA confirmed a new asteroid trajectory"*).
   - Classifies claim type (`factual`, `medical_factual`, `subjective_opinion`), formulates search queries, fetches web candidates and optional Google Fact Check API items, ranks evidence, and performs grounded verification.

2. **URL Verification Mode**:
   - **URL-Only**: Fetches a public webpage safely, extracts bounded key factual claims, independently verifies each claim across external web sources, and aggregates an overall article-level verdict.
   - **URL + Question**: Uses fetched webpage content as context to resolve contextual questions (e.g., *"Is this statement accurate?"*), then independently verifies the resolved claim while excluding the exact subject page from independent evidence to prevent circular self-proof.

3. **Image OCR Mode**:
   - Accepts uploaded image files or base64 image payloads.
   - Uses **RapidOCR** (`rapidocr-onnxruntime`) with system `pytesseract` fallback to extract visible text from screenshots, news clips, or document flyers.
   - Classifies question intent (`text_extraction`, `fact_check_verify`, `visual_question`, `specific_question`).
   - Extracts verifiable claim propositions (`extract_ocr_claim_proposition`) from image text and routes them through the verification pipeline.
   - *Scope Note*: Image analysis focuses primarily on extracting and verifying factual text from images.

4. **Speech-to-Text (STT) Mode**:
   - Integrated directly in the frontend claim input interface (`frontend/src/components/ClaimInput.tsx`).
   - Utilizes browser-native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) configured for English (`en-IN` default).
   - Allows users to speak claims via microphone, transcribing spoken audio into the text area in real-time before submitting to the verification pipeline.

---

## 🚦 Verdicts & Terminology

The system outputs a structured verdict representing the verification outcome. 

### Internal vs. User-Facing Verdict Vocabulary

| Backend Enum Value (`AssessmentVerdict`) | User-Facing Display Label | Symbol | Description |
| :--- | :--- | :---: | :--- |
| `supported` | **Supported** | 🟢 | Direct, reliable evidence from primary or secondary sources explicitly corroborates the claim. |
| `contradicted` | **Contradicted** | 🔴 | Direct, reliable evidence explicitly refutes, disproves, or establishes facts incompatible with the claim. |
| `insufficient_evidence` | **No Official Evidence** | 🟡 | The system could not establish sufficient authoritative evidence to confirm or refute the claim. |
| `conflicting_evidence` | **Conflicting Evidence** | 🟠 | High-credibility sources directly contradict one another or present conflicting empirical findings. |
| `subjective_opinion` | **Subjective / Opinion** | 🔵 | The statement expresses a value judgment, qualitative framing, or opinion that is not objectively verifiable. |

> **Important UX Distinction**: The backend schema uses `insufficient_evidence` internally, but the user interface renders **"No Official Evidence"** to clearly communicate to users that no decisive official reporting was found in indexed web sources.

---

## 🔬 Evidence & Source Quality Principles

### Source Authority Tiering
Domains are categorized into three explicit authority tiers (`core/source_filter.py`):

- **PRIMARY** (Authority Weight: `1.0`): Official government domains (`.gov`, `.gov.in`, `.nic.in`, `.edu`, `.ac.in`), official registries (WHO, UN, CDC, FDA, NIH, NASA, RBI, ISRO), and legal court repositories.
- **SECONDARY** (Authority Weight: `0.85`): Established international news wire services, recognized journalism outlets, and established fact-checking organizations (Reuters, AP, BBC, The Hindu, Bloomberg, Snopes, FactCheck.org, PolitiFact, etc.).
- **LOW_CONFIDENCE** (Authority Weight: `0.4`): User-generated content platforms, social networks, forums, and unverified personal blogs (Reddit, Twitter/X, Facebook, Medium, Quora, Blogspot, YouTube, etc.). Unknown or unclassified domains default conservatively to LOW_CONFIDENCE.

*Role in Verification*: Source authority weights scale passage similarity scores during ranking. Low-confidence sources receive stricter relevance thresholds and should not serve as the sole basis for strong factual conclusions.

---

## 📊 BGE-M3 Semantic Ranking

Semantic ranking evaluates candidate passages using `BAAI/bge-m3` embeddings (`core/ranker.py`):

- **Embedding & Scoring**: Computes cosine similarity between the claim vector and passage vectors using Hugging Face Inference API or local `SentenceTransformer` models (with a lightweight lexical fallback if models are offline or in low-memory mode).
- **Metric Distinction**:
  - **Relevance Score (% Relevance)**: Measures textual and topical similarity between the claim and an evidence passage.
  - **Confidence Score**: Verification confidence is an internal confidence signal associated with the generated assessment and should not be interpreted as a calibrated probability that the claim is true.
- **Crucial Boundary**: BGE-M3 semantic similarity measures how relevant/semantically related retrieved evidence is to the claim; it is not a truth probability.

---

## 🚪 Evidence Quality Gate

Candidate evidence items must pass conservative quality checks before LLM analysis (`core/evidence_gate.py`):

- **URL Validity**: Rejects invalid, empty, or malformed URLs (`is_valid_url`).
- **Minimum Passage Length**: Rejects snippets under 10 words.
- **Duplicate Filtering**: Deduplicates identical passage text across candidate search hits.
- **Tier-Dependent Relevance Thresholds**:
  - Primary sources: minimum relevance score `0.15`
  - Secondary sources: minimum relevance score `0.25`
  - Low-confidence sources: minimum relevance score `0.45`

---

## 🤖 LLM Verification & Fallback

- **Configured Model**: `meta-llama/Llama-3.3-70B-Instruct` (via Hugging Face `InferenceClient`).
- **Grounded Verification**: System prompts instruct the LLM to evaluate logical stance (`supports`, `contradicts`, `neutral`) strictly against text inside `Passage: "..."`. Domain names, URLs, and article titles serve provenance context only and are not treated as proof.
- **Heuristic Fallback Mode**: If Hugging Face verification is unavailable, the pipeline can fall back to the implemented heuristic verifier (`analyze_with_heuristics`). This is a degraded mode and is less nuanced and reliable than the primary LLM verification path.

---

## 🔍 Google Fact Check Integration

When `GOOGLE_FACT_CHECK_API_KEY` is configured, the system can query the Google Fact Check Tools API for published fact-check reviews matching the claim.

Returned reviews can include the reviewed claim, publisher, rating, review URL, and normalized verdict signal.

These reviews are incorporated as an additional fact-check signal. A fact-check result should not be interpreted as automatic proof of the user's claim because the reviewed claim may differ in wording, scope, date, or context.

The integration is optional and does not replace independent web evidence retrieval.

---

## 🌐 URL Verification & Security

- **Safe Web Fetching**: Fetches public webpages via `httpx` with timeout controls and extracts metadata (`og:title`, `<title>`, canonical URL, publication date, author) and cleaned text via BeautifulSoup4 (`core/url_fetcher.py`).
- **SSRF Protection**: `is_safe_public_url` validates hostnames and blocks requests targeting localhost, private subnets (`10.x`, `172.16-31.x`, `192.168.x`), loopback addresses (`127.0.0.1`, `::1`), link-local IPs, or DNS entries resolving to private IPs.
- **Subject-Page Isolation**: When analyzing a user-supplied URL, that exact page and its canonical URL are excluded from independent evidence search (`is_subject_page_url`) so the page cannot act as circular proof for its own claims.

---

## 🖼️ Image & OCR Pipeline

- **OCR Engine**: Uses **RapidOCR** (`rapidocr-onnxruntime`) as primary engine, with system `pytesseract` as fallback (`core/image_ocr.py`).
- **Preprocessing**: Image upscaling (if under 600x300), RGB conversion, autocontrast, and header/footer UI noise removal (`clean_extracted_ocr_text`).
- **Intent Routing**:
  - `text_extraction`: Returns raw extracted OCR text.
  - `fact_check_verify`: Extracts verifiable claim propositions (`extract_ocr_claim_proposition`) and executes full verification.
  - `visual_question`: Calls multimodal vision endpoint if `HF_VISION_MODEL` is configured, or returns an explicit limitation noting that visual spatial reasoning is unconfigured.
  - `specific_question`: Verifies the resolved claim or question against web evidence.

---

## 🎤 Speech-to-Text (STT)

- **Frontend Component**: Implemented in `frontend/src/components/ClaimInput.tsx`.
- **Engine**: Browser-native Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`).
- **Interface**: Microphone icon button (`<Mic />`) embedded in the main claim input box.
- **Behavior**: Listens to user voice input in real-time, converts speech to text, updates the input area, and enables one-click submission to the verification pipeline.
- **Browser Requirements**: Requires browser Web Speech API support (Google Chrome, Microsoft Edge, Safari) and user microphone permissions.

---

## 🔌 API Reference

FastAPI backend endpoints (`api/main.py`):

### `GET /`
Returns API running status and OpenAPI documentation URL (`/docs`).

### `GET /api/health`
Returns system operational status, HF token configuration state, and configured model identifiers:
```json
{
  "status": "healthy",
  "hf_token_configured": true,
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct",
  "embedding_model": "BAAI/bge-m3"
}
```

### `POST /api/analyze`
Main analysis endpoint accepting JSON payloads for claims, URLs, or base64 images.

**Request Schema Placeholder**:
```json
{
  "claim": "<textual claim or URL string>",
  "image_base64": "<optional base64 image string>",
  "image_filename": "<optional image filename>",
  "question": "<optional question about claim or image>"
}
```

**Response Schema Structure (`AnalysisResult`)**:
```json
{
  "claim": "<analyzed claim proposition>",
  "claim_type": "factual | medical_factual | subjective_opinion",
  "verdict": "supported | contradicted | insufficient_evidence | conflicting_evidence | subjective_opinion",
  "verdict_symbol": "🟢 | 🔴 | 🟡 | 🟠 | 🔵",
  "verdict_title": "<verdict title string>",
  "confidence_score": "<runtime value>",
  "explanation": "<detailed evidence-grounded breakdown>",
  "supporting_evidence": [
    {
      "id": "<evidence ID>",
      "url": "<evidence URL>",
      "title": "<article title>",
      "domain": "<source domain>",
      "source_tier": "primary | secondary | low_confidence",
      "passage": "<extracted evidence snippet>",
      "similarity_score": "<runtime value>",
      "stance": "supports | contradicts | neutral",
      "stance_explanation": "<reasoning for stance>"
    }
  ],
  "contradicting_evidence": [],
  "evidence_limitations": ["<limitation or gap in evidence>"],
  "all_sources": [
    {
      "url": "<source URL>",
      "domain": "<domain>",
      "title": "<title>",
      "tier": "primary | secondary | low_confidence",
      "tier_reason": "<tier classification explanation>"
    }
  ],
  "latency_seconds": "<runtime value>",
  "mode": "claim | url | url_question | image",
  "targeted_answer": "<direct answer statement>"
}
```

### `POST /api/analyze-image`
Multipart form-data upload endpoint for image analysis.

**Parameters**:
- `file`: Image file payload (`multipart/form-data`)
- `question`: Optional question string (`Form`)

---

## ⚙️ Configuration

Managed via environment variables (`core/config.py` and `.env.example`).

### Configuration Variables Matrix

| Variable | Source Code Default | `.env.example` Value | Description |
| :--- | :--- | :--- | :--- |
| `HF_TOKEN` | `""` | `your_huggingface_token_here` | Hugging Face Access Token for LLM & embedding Inference API. |
| `GOOGLE_FACT_CHECK_API_KEY` | `""` | `your_google_api_key_here` | Optional API key for Google Fact Check Tools API. |
| `HF_LLM_MODEL` | `meta-llama/Llama-3.3-70B-Instruct` | `meta-llama/Llama-3.3-70B-Instruct` | Hugging Face model identifier for verification. |
| `HF_EMBEDDING_MODEL` | `BAAI/bge-m3` | `BAAI/bge-m3` | Embedding model identifier for BGE-M3 ranking. |
| `MAX_SEARCH_RESULTS` | `5` | `5` | Maximum web search candidates retrieved per claim. |
| `TOP_K_EVIDENCE` | `6` | `4` | Maximum evidence chunks selected for LLM verification; `.env.example` explicitly overrides the code default to 4. |
| `HTTP_TIMEOUT` | `6.0` | `6.0` | HTTP request timeout in seconds for web fetching. |
| `LOW_MEMORY_MODE` | `true` | `true` | Optimizes memory usage by disabling heavy local model loads. |
| `ALLOW_MOCK_FALLBACK` | `true` | `true` | Enables heuristic fallback mode when `HF_TOKEN` is absent or rate-limited. |
| `ALLOWED_ORIGINS` | `""` | `https://hack-xi-red.vercel.app,http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins for FastAPI middleware. |

---

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Clone & Virtual Environment
```bash
git clone https://github.com/educational454-ai/hack.git
cd hack

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt
```

### 2. Configure Environment File
```bash
cp .env.example .env
```
Edit `.env` to set your credentials:
```env
HF_TOKEN=your_huggingface_token_here
GOOGLE_FACT_CHECK_API_KEY=your_google_api_key_here
```

### 3. Start Backend Server
```bash
python run_server.py
```
The FastAPI backend server runs at `http://127.0.0.1:8000`. OpenAPI docs are available at `http://127.0.0.1:8000/docs`.

### 4. CLI Analyzer (Optional Terminal Testing)
```bash
python cli.py "Is India a member of the UN Security Council permanent five?"
```

### 5. Start Frontend Application
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing & CI

### Run Backend Unit Tests
Execute the backend unit test suite:
```bash
python -m unittest discover -s tests
```

### Run Frontend Build
Validate TypeScript compilation and Vite production build:
```bash
cd frontend
npm run build
```

### Continuous Integration (CI)
GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs on main pushes and pull requests:
- **backend-test**: Sets up Python 3.12, installs dependencies, and runs `python -m unittest discover -s tests`.
- **frontend-build**: Sets up Node.js 20, installs npm dependencies, and runs `npm run build`.

---

## 🔐 Security & Trust Boundaries

- **Untrusted Web Inputs**: All external web HTML content and extracted text are sanitized and cleaned before parsing.
- **SSRF Defense**: `is_safe_public_url` validates URLs against localhost, private IP subnets (`10.x`, `172.16-31.x`, `192.168.x`), loopback addresses (`127.0.0.1`, `::1`), and private DNS resolutions.
- **Citation Provenance Validation**: `_validate_llm_provenance` checks model citation references against retrieved evidence IDs, rejecting hallucinated IDs.
- **Environment Isolation**: API secrets (`HF_TOKEN`, `GOOGLE_FACT_CHECK_API_KEY`) are managed via `.env` and never exposed in client responses.

---

## ⚠️ System Boundaries & Limitations

- **Web Search Dependency**: Web retrieval quality depends on live DuckDuckGo Search reachability and public web indexing.
- **LLM Rate Limits & Quotas**: Serverless Hugging Face Inference API calls require an active `HF_TOKEN` and depend on model server availability.
- **Heuristic Fallback Trade-off**: The heuristic fallback mode is an offline degraded mode and is less nuanced and reliable than the primary Llama 3.3 70B verification path.
- **OCR Quality**: Text extraction from images depends on image resolution, contrast, and layout clarity.
- **Speech Recognition Browser Constraints**: Speech-to-text relies on browser Web Speech API support (Chrome, Edge, Safari) and requires microphone permissions.
- **Semantic Relevance vs. Truth**: BGE-M3 embedding similarity measures topical closeness, not factual accuracy.

---

## 💡 Hackathon Demo Walkthrough

A practical 4-step demonstration flow:

1. **Text Claim Verification**:
   - Enter a factual claim (e.g., *"The Earth orbits the Sun"*).
   - Observe live web search, domain authority tiering, evidence passage ranking, and grounded verdict output.
2. **URL Verification**:
   - Paste an article URL to extract key factual claims and run independent verification with subject page isolation.
3. **Image OCR Verification**:
   - Upload a flyer image or news clip screenshot to extract readable text claims and verify them against web evidence.
4. **Speech-to-Text Voice Input**:
   - Click the microphone icon (`<Mic />`) in the claim input box, speak a claim aloud, and watch it transcribe in real-time before analyzing.

---

## 📁 Project Structure

```
hack/
├── .env.example              # Template for environment configuration
├── requirements.txt          # Backend Python dependencies
├── run_server.py             # FastAPI backend launcher
├── cli.py                    # Terminal CLI analyzer tool
├── api/
│   ├── __init__.py
│   └── main.py               # FastAPI endpoint handlers (/api/health, /api/analyze, /api/analyze-image)
├── core/
│   ├── __init__.py
│   ├── config.py             # Configuration dataclass & env loader
│   ├── schemas.py            # Pydantic data contracts (AnalysisResult, EvidenceItem, etc.)
│   ├── claim_parser.py       # Claim classification & query formulation
│   ├── retriever.py          # DDGS text & image retrieval
│   ├── source_filter.py      # Domain tiering (Primary, Secondary, Low-Confidence)
│   ├── extractor.py          # HTML cleaning, passage chunking & parallel web fetching
│   ├── ranker.py             # BGE-M3 semantic similarity scoring & image ranking
│   ├── evidence_gate.py      # Evidence Quality Gate filtering
│   ├── verifier.py           # HF LLM comparative analysis & heuristic fallback
│   ├── pipeline.py           # Core pipeline orchestration & entrypoint
│   ├── fact_check_api.py     # Google Fact Check Tools API integration
│   ├── url_normalizer.py     # URL normalization & equivalence helpers
│   ├── url_fetcher.py        # Webpage fetcher with SSRF protection & metadata parser
│   ├── url_pipeline.py       # URL & URL+Question mode handlers
│   ├── image_ocr.py          # RapidOCR & pytesseract text extraction engine
│   └── image_pipeline.py     # Multimodal image verification pipeline
├── frontend/                 # React 19 + TypeScript + Vite web application
│   ├── src/
│   │   ├── components/       # ClaimInput, ResultCard, LeftSidebar, RightSidebar, LandingPage
│   │   ├── types.ts          # TypeScript interfaces
│   │   ├── api.ts            # Frontend API client
│   │   ├── App.tsx           # Main application layout & router
│   │   └── index.css         # Design system & styles
│   ├── package.json
│   └── vite.config.ts
├── tests/                    # Backend unit test suite
│   ├── test_api.py
│   ├── test_evidence_gate.py
│   ├── test_image_input.py
│   ├── test_image_relevance.py
│   ├── test_parser.py
│   ├── test_pipeline.py
│   ├── test_relevance_and_caveats.py
│   ├── test_source_filter.py
│   ├── test_url_verification.py
│   └── test_verifier.py
└── .github/
    └── workflows/
        └── ci.yml            # GitHub Actions CI workflow
```