# Evidence-First AI Misinformation Analyzer (AI-03)

An **evidence-first** misinformation detection and verification engine. Unlike static LLM-based fact-checkers that rely on parametric memory (susceptible to hallucinations, temporal decay, and ungrounded assertions), TruthGuard AI executes an end-to-end multi-stage pipeline: real-time web retrieval, source authority classification, content extraction, semantic relevance ranking, quality gate filtering, grounded LLM analysis, and provenance validation.

---

## 🎯 What It Does

- **Real-Time Evidence Retrieval**: Searches live web sources per query rather than relying on frozen training parameters.
- **Strict Evidence Grounding**: Verdict decisions and explanations are anchored in extracted evidence passages.
- **Source Authority Classification**: Evaluates source reliability across government, academic, major news, and user-generated tiers.
- **Provenance Validation**: Validates all model-cited evidence IDs against retrieved passages to eliminate hallucinated citations.
- **Multimodal & Multi-Format Verification**: Supports plain text claims, webpage URLs, URL + contextual questions, and image OCR claims or flyers.
- **Transparent Output**: Returns non-binary verdicts, confidence scores, semantic relevance percentages, evidence passages, source lists, and explicit limitations.

---

## ⚙️ How It Works

### System Architecture

```
                      [User Input: Claim / URL / Image Payload]
                                          │
                                          ▼
                              [Input Mode Detection]
                                          │
    ┌───────────────────────────────┬─────┴───────────────────────────────┐
    ▼                               ▼                                     ▼
[Text Claim Mode]         [URL Verification Mode]             [Image OCR Mode]
    │                               │                                     │
    ▼                               ▼                                     ▼
[Claim Classification]    [Safe Page Fetch & Context]      [RapidOCR Text Extraction]
    │                               │                                     │
    ▼                               ▼                                     ▼
[Real Web Search]         [Independent Evidence Search]    [Claim Proposition Extraction]
 (DDGS + Google Fact Check)          │                                     │
    │                               │                                     │
    └───────────────────────────────┼─────────────────────────────────────┘
                                    │
                                    ▼
                         [Source Quality Tiering]
                         (Primary / Secondary / Low Confidence)
                                    │
                                    ▼
                       [Content Passage Extraction]
                       (HTML Cleaning & Word Chunking)
                                    │
                                    ▼
                       [BGE-M3 Semantic Ranking]
                       (SentenceTransformers / HF API / Cosine Sim)
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
                     [Provenance & Schema Validation]
                     (Citation ID Mapping & Stance Consistency)
                                    │
                                    ▼
                     [Structured Verdict + Synthesis]
```

---

## 📥 Input Modes

1. **Text Claim Mode**:
   - Accepts plain-text statements (e.g., *"NASA confirmed a new asteroid trajectory"*).
   - Classifies claim type (`factual`, `medical_factual`, `subjective_opinion`), extracts targeted search queries, retrieves web search candidates and optional Google Fact Check API items, ranks evidence, and performs grounded verification.

2. **URL Verification Mode**:
   - **URL-Only**: Fetches a public webpage safely, extracts bounded key factual claims, independently verifies each claim across external sources, and aggregates an overall article-level verdict.
   - **URL + Question**: Uses fetched webpage content as context to resolve contextual questions (e.g., *"Is this statement accurate?"*), then independently verifies the resolved claim while excluding the exact subject page from independent evidence to prevent circular proof.

3. **Image OCR Mode**:
   - Accepts uploaded images or base64 image payloads.
   - Uses **RapidOCR** (with system `pytesseract` fallback) to extract readable text from screenshots, news clips, or document flyers.
   - Classifies question intent (`text_extraction`, `fact_check_verify`, `visual_question`, `specific_question`).
   - Extracts verifiable claim propositions from image text and routes them through the evidence verification pipeline.
   - *Scope Note*: Image analysis focuses primarily on extracting and verifying factual text from images.

---

## 🚦 Supported Verdict Types

The system outputs a structured verdict from a non-binary 5-type vocabulary:

| Verdict | Symbol | Description |
| :--- | :---: | :--- |
| **Supported** | 🟢 | Direct, reliable evidence from primary or secondary sources explicitly corroborates the core claim proposition. |
| **Contradicted** | 🔴 | Direct, reliable evidence explicitly refutes, disproves, or establishes facts incompatible with the claim. |
| **Insufficient Evidence** | 🟡 | Available retrieved evidence is incomplete, ambiguous, or lacks explicit facts to confirm or refute the claim. |
| **Conflicting Evidence** | 🟠 | High-credibility sources directly contradict one another or present conflicting empirical findings. |
| **Subjective / Opinion** | 🔵 | The statement expresses a value judgment, qualitative framing, or opinion that is not objectively verifiable. |

*Why "Insufficient Evidence" exists*: Not all claims have indexed or conclusive web documentation. When search retrieval produces no matching records or only low-confidence sources, the system explicitly returns `insufficient_evidence` rather than guessing or hallucinating a verdict.

---

## 🔬 Evidence & Source Quality Principles

### Source Tiering
Sources are categorized into three distinct authority tiers (`core/source_filter.py`):

- **PRIMARY** (Authority Weight: `1.0`): Official government domains (`.gov`, `.gov.in`, `.nic.in`, `.edu`, `.ac.in`), official registries (WHO, UN, CDC, FDA, NIH, NASA, RBI, ISRO), and legal repositories.
- **SECONDARY** (Authority Weight: `0.85`): Established news agencies, wire services, and recognized fact-checking organizations (Reuters, AP, BBC, The Hindu, Bloomberg, Snopes, FactCheck.org, PolitiFact, etc.).
- **LOW_CONFIDENCE** (Authority Weight: `0.4`): User-generated content platforms, social networks, forums, and unverified personal blogs (Reddit, Twitter/X, Facebook, Medium, Quora, Blogspot, etc.). Unknown domains default conservatively to LOW_CONFIDENCE.

*Role in Verification*: Source tiering adjusts passage similarity scores and enforces quality gates. A claim cannot be marked `supported` or `contradicted` based solely on low-confidence sources without primary or secondary corroboration.

---

## 📊 BGE-M3 Semantic Ranking

Semantic ranking uses `BAAI/bge-m3` embeddings (`core/ranker.py`):

- **Purpose**: Measures topic and textual similarity (0.0 to 1.0) between the user claim and retrieved passages to select the top-K most relevant chunks for LLM verification.
- **Distinct Metrics**:
  - **Relevance Score (% Relevance)**: Indicates how topically close an evidence passage is to the claim assertion.
  - **Confidence Score**: Indicates the verifier's confidence in the final verdict based on evidence authority, tier weighting, and source agreement. High relevance does not imply a claim is true.

---

## 🚪 Evidence Quality Gate

Candidate evidence items must pass conservative quality checks before LLM analysis (`core/evidence_gate.py`):

- **URL Validity**: Rejects invalid, empty, or malformed URLs (`is_valid_url`).
- **Minimum Word Count**: Rejects passages with fewer than 10 words.
- **Duplicate Detection**: Filters near-duplicate passage texts across candidates.
- **Tier-Dependent Relevance Thresholds**:
  - Primary sources: minimum relevance score `0.15`
  - Secondary sources: minimum relevance score `0.25`
  - Low-confidence sources: minimum relevance score `0.45`

---

## 🤖 LLM Verification

- **Configured Model**: `meta-llama/Llama-3.3-70B-Instruct` (via Hugging Face `InferenceClient`).
- **Grounded Verification**: System prompts instruct the LLM to evaluate logical entailment (`supports`, `contradicts`, `neutral`) strictly against the retrieved passage text inside `Passage: "..."`. Domain names, URLs, and article titles are for provenance only and are not treated as factual proof.
- **Heuristic Fallback**: If `HF_TOKEN` is unconfigured, rate-limited, or offline, the pipeline falls back to an intelligent semantic heuristic verifier (`analyze_with_heuristics`).

---

## 🛡️ Provenance Validation

The system enforces strict runtime provenance tracking (`_validate_llm_provenance`):

- LLM evidence references (e.g., `ev_1`, `ev_2`) are matched against actual retrieved `EvidenceItem` objects by exact ID, index, or URL.
- Raw LLM JSON outputs are **never** allowed to instantiate new or synthetic evidence items.
- Unmappable or hallucinated citation IDs are rejected and recorded under `evidence_limitations`.

---

## 🌐 URL Verification & Safety

- **Modes**: URL-only claim extraction & URL + Question contextual analysis (`core/url_pipeline.py`).
- **Safe Page Fetching**: Uses `httpx` and `BeautifulSoup4` to extract titles, canonical URLs, publication dates, authors, and main article text (`core/url_fetcher.py`).
- **SSRF Protections**: `is_safe_public_url` validates URLs and blocks requests to loopback addresses, local network IPs (`127.0.0.1`, `localhost`, RFC1918 private subnets), link-local addresses, and DNS hostnames resolving to private IPs.
- **Subject-Page Isolation**: When verifying a URL, the exact subject page URL and its canonical equivalent are excluded from independent evidence retrieval (`is_subject_page_url`) to avoid circular self-referential proof.

---

## 🖼️ Image Verification & OCR

- **OCR Engine**: Uses **RapidOCR** (`rapidocr-onnxruntime`) as primary engine, with system `pytesseract` as fallback (`core/image_ocr.py`).
- **Preprocessing & Cleaning**: Image upscaling, RGB normalization, autocontrast, and header/footer noise removal (`clean_extracted_ocr_text`).
- **Question Intent Routing**:
  - `text_extraction`: Returns raw extracted OCR text.
  - `fact_check_verify`: Extracts core factual claim proposition (`extract_ocr_claim_proposition`) and executes verification.
  - `visual_question`: Uses multimodal vision model if configured (`HF_VISION_MODEL`), or returns an explicit limitation explaining that visual spatial reasoning is unconfigured.
  - `specific_question`: Verifies the resolved claim or question against web evidence.
- **Boundary**: Image verification focuses on extracting and verifying factual text claims from image media.

---

## 🔌 API Reference

The FastAPI backend (`api/main.py`) provides the following endpoints:

### `GET /`
Returns basic API status and links to interactive documentation (`/docs`).

### `GET /api/health`
Returns health status, HF token configuration status, and active LLM/embedding model names:
```json
{
  "status": "healthy",
  "hf_token_configured": true,
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct",
  "embedding_model": "BAAI/bge-m3"
}
```

### `POST /api/analyze`
Main verification endpoint accepting JSON payloads for claims, URLs, or base64 images.

**Request Payload Examples**:

*Text Claim*:
```json
{
  "claim": "NASA confirmed a new asteroid trajectory in 2026."
}
```

*Image Payload*:
```json
{
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "image_filename": "flyer.png",
  "question": "Is this claim real?"
}
```

**Response Payload Structure (`AnalysisResult`)**:
```json
{
  "claim": "NASA confirmed a new asteroid trajectory in 2026.",
  "claim_type": "factual",
  "verdict": "supported",
  "verdict_symbol": "🟢",
  "verdict_title": "Supported",
  "confidence_score": 0.88,
  "explanation": "Yes, NASA confirmed a new asteroid trajectory. Verified reports and empirical documentation from nasa.gov explicitly confirm the stated event.",
  "supporting_evidence": [
    {
      "id": "ev_1",
      "url": "https://www.nasa.gov/news/asteroid-trajectory-2026",
      "title": "NASA Asteroid Trajectory Update",
      "domain": "nasa.gov",
      "source_tier": "primary",
      "passage": "NASA Climate Monitoring and Planetary Defense teams published confirmed trajectory observations...",
      "similarity_score": 0.84,
      "stance": "supports",
      "stance_explanation": "Authoritative primary report explicitly corroborates the trajectory observation."
    }
  ],
  "contradicting_evidence": [],
  "evidence_limitations": [],
  "all_sources": [
    {
      "url": "https://www.nasa.gov/news/asteroid-trajectory-2026",
      "domain": "nasa.gov",
      "title": "NASA Asteroid Trajectory Update",
      "tier": "primary",
      "tier_reason": "Official Source: Official government authority, academic publication, or recognized legal repository."
    }
  ],
  "relevant_images": [],
  "latency_seconds": 3.42,
  "mode": "claim",
  "targeted_answer": "Yes, NASA confirmed a new asteroid trajectory."
}
```

### `POST /api/analyze-image`
Multipart form-data endpoint for direct image file uploads.

**Parameters**:
- `file`: Uploaded image file (`multipart/form-data`)
- `question` (optional): User question string

---

## 🖥️ Frontend Overview

Built with **React 19**, **TypeScript**, and **Vite**:

- **Landing Page** (`LandingPage.tsx`): Pinterest-style editorial visual presentation across 5 core sections:
  1. Hero / Why (Masthead typography & overlapping visual collage)
  2. Evidence Engine (Layered asymmetric evidence board)
  3. Quote Stage (3D stacked magazine carousel with WHO & UN quotes)
  4. Analyzer Showcase (Interactive product interface frame)
  5. Multimodal & Traceability (Media collage: Image OCR, Document, URL, Traceability chain)
  6. Final CTA (Poster-like closing frame)
- **Analyzer Application** (`/analyzer` route):
  - Tabbed input controls for Text Claim, Web URL, and Image Upload.
  - Interactive pipeline step execution indicators.
  - Result card displaying verdict symbols, confidence badges, direct answers, and AI summaries.
  - Evidence cards with relevance scores, source tier tags, and expandable quotes.
  - All Sources drawer & image preview thumbnails.
  - Left sidebar with architectural principles & recent analysis history.

---

## ⚙️ Configuration

Settings are managed via environment variables (`core/config.py` & `.env.example`).

### Required / Core Settings
- `HF_TOKEN`: Hugging Face User Access Token (required for Hugging Face LLM and BGE-M3 API calls).

### Optional API Integration
- `GOOGLE_FACT_CHECK_API_KEY`: API key for Google Fact Check Tools API (free, 1000 req/day).

### Model Configuration
- `HF_LLM_MODEL`: Hugging Face LLM model identifier (default: `meta-llama/Llama-3.3-70B-Instruct`).
- `HF_EMBEDDING_MODEL`: Embedding model identifier (default: `BAAI/bge-m3`).

### Pipeline & Performance Settings
- `MAX_SEARCH_RESULTS`: Max web search candidates to retrieve per claim (default: `5`).
- `TOP_K_EVIDENCE`: Max evidence chunks to select for LLM verification (default: `4`).
- `HTTP_TIMEOUT`: Web fetch timeout in seconds (default: `6.0`).
- `LOW_MEMORY_MODE`: Set to `true` to optimize memory usage (default: `true`).
- `ALLOW_MOCK_FALLBACK`: Enables heuristic fallback mode when `HF_TOKEN` is unconfigured or rate-limited (default: `true`).
- `ALLOWED_ORIGINS`: Comma-separated CORS origins for frontend access (default: `https://hack-xi-red.vercel.app,http://localhost:5173,http://127.0.0.1:5173`).

---

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Repository Setup & Environment
```bash
git clone https://github.com/SOHAN-AI/hackathon.git
cd hackathon

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
Edit `.env` and set your credentials:
```env
HF_TOKEN=your_huggingface_token_here
GOOGLE_FACT_CHECK_API_KEY=your_google_api_key_here
```

### 3. Run Backend Server
```bash
python run_server.py
```
The FastAPI backend server will run at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

### 4. Run CLI Interface (Optional)
To test verification directly in your terminal:
```bash
python cli.py "Is India a member of the United Nations Security Council permanent five?"
```

### 5. Run Frontend Development Server
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

### Backend Test Suite
Run the backend unit test suite:
```bash
python -m unittest discover -s tests
```

### Frontend Build Validation
Compile TypeScript and build the production bundle:
```bash
cd frontend
npm run build
```

---

## 🔄 CI

Automated continuous integration is configured via GitHub Actions (`.github/workflows/ci.yml`):
- **backend-test**: Sets up Python 3.12, installs `requirements.txt`, and executes `unittest discover -s tests`.
- **frontend-build**: Sets up Node.js 20, installs dependencies (`npm ci`), and verifies production build (`npm run build`).

---

## ⚠️ Limitations

- **Search Availability**: Web retrieval depends on DuckDuckGo Search availability and network reachability.
- **LLM API Quotas**: Serverless Hugging Face Inference API calls require an active `HF_TOKEN` and depend on model endpoint availability.
- **Source Indexing**: The system cannot verify claims if relevant authoritative primary or secondary web sources are unindexed or unavailable.
- **OCR Text Focus**: Image verification relies on OCR text extraction (screenshots, flyers, clips) rather than unrestricted visual scene understanding.

---

## 💡 Hackathon Demo Usage

Example claims to test in the Analyzer interface:

1. **Factual Claim**: *"The Earth orbits the Sun."*
   - Expected Output: `Supported` (🟢) with primary/secondary scientific evidence citations.
2. **False / Contradicted Claim**: *"The Sun orbits the Earth."*
   - Expected Output: `Contradicted` (🔴) with evidence refuting geocentrism.
3. **Subjective Claim**: *"Mumbai is the best city in India."*
   - Expected Output: `Subjective / Opinion` (🔵) explaining qualitative value judgment framing.
4. **Image OCR Verification**:
   - Upload a document flyer or news screenshot containing text to extract and verify factual statements.

---

## 🔐 Security & Trust Boundaries

- **Runtime Web Search**: No hardcoded evidence; candidates are gathered live per request.
- **Provenanced Citations**: Model output citations are validated against retrieved evidence IDs before rendering.
- **SSRF Defense**: Restricts webpage fetching from targeting private, loopback, or local IP networks.
- **Environment Isolation**: API tokens are loaded from `.env` and excluded from frontend client responses.

---

## 📁 Project Structure

```
hackathon/
├── .env.example              # Template for environment configuration
├── requirements.txt          # Backend Python dependencies
├── run_server.py             # Server startup script for FastAPI
├── cli.py                    # Terminal CLI analyzer script
├── api/
│   ├── __init__.py
│   └── main.py               # FastAPI routes (/api/health, /api/analyze, /api/analyze-image)
├── core/
│   ├── __init__.py
│   ├── config.py             # Configuration dataclass & env loader
│   ├── schemas.py            # Pydantic data contracts (AnalysisResult, EvidenceItem, etc.)
│   ├── claim_parser.py       # Claim classification & search query formulation
│   ├── retriever.py          # DDGS text & image search retrieval
│   ├── source_filter.py      # Domain tiering (Primary, Secondary, Low Confidence)
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
├── frontend/                 # React 19 + TypeScript + Vite web app
│   ├── src/
│   │   ├── components/       # UI components & LandingPage
│   │   ├── types.ts          # TypeScript interfaces
│   │   ├── api.ts            # Frontend API client
│   │   ├── App.tsx           # Main application router/layout
│   │   └── index.css         # Styling design system
│   ├── package.json
│   └── vite.config.ts
└── tests/                    # Backend unit test suite
    ├── test_api.py
    ├── test_evidence_gate.py
    ├── test_image_input.py
    ├── test_image_relevance.py
    ├── test_parser.py
    ├── test_pipeline.py
    ├── test_relevance_and_caveats.py
    ├── test_source_filter.py
    ├── test_url_verification.py
    └── test_verifier.py
```