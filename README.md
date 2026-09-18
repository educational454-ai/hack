# Evidence-First AI Misinformation Analyzer (AI-03)

An **evidence-first** misinformation detection and verification engine. Unlike traditional "LLM-first" fact-checkers that rely on static parametric memory—suffering from hallucinations, outdated facts, and temporal decay—AI-03 follows a strictly grounded, multi-stage verification pipeline:

```
[User Input: Claim / URL / URL + Question]
                    │
                    ▼
          [Input Mode Detection]
                    │
   ┌────────────────┴────────────────┐
   ▼                                 ▼
[Claim Verification Mode]   [URL Verification Mode]
   │                                 │
   ▼                                 ▼
[Claim Classification]      [Safe Page Fetch & Context]
   │                                 │
   ▼                                 ▼
[Real Web Search (DDGS)]    [Independent Evidence Search]
   │                                 │
   └────────────────┬────────────────┘
                    │
                    ▼
       [Source Quality Tiering]
                    │
                    ▼
       [Content Passage Extraction]
                    │
                    ▼
     [BGE-M3 Semantic Similarity]
                    │
                    ▼
       [Evidence Quality Gate]
                    │
                    ▼
  [HF Verification: Llama-3.3-70B]
                    │
                    ▼
   [Provenance & Schema Validation]
                    │
                    ▼
    [Structured Verdict + Synthesis]
```

---

## 🎯 Key Capabilities

1. **Multi-Mode Input Support**:
   - **Claim Mode**: Analyzes plain-text factual or opinion statements (e.g., *"India banned UPI in 2025"*).
   - **URL-Only Mode**: Fetches a public webpage, extracts bounded key factual claims, and evaluates an article-level verification overview.
   - **URL + Question Mode**: Uses webpage context to ground user questions, while performing independent verification search that isolates the subject webpage.

2. **Authoritative Source Tiering**:
   - **Primary**: Official government bureaus (`.gov`, `.gov.in`, PIB, RBI, legal courts) and peer-reviewed scientific databases.
   - **Secondary**: Reputable international journalism and wire agencies (Reuters, AP, BBC, The Hindu, etc.).
   - **Low-Confidence**: Social media, forums (Reddit, X), unverified blogs, and speculative commentary.

3. **BGE-M3 Semantic Relevance Ranking**:
   - Uses `BAAI/bge-m3` embedding similarity to extract topically relevant 150–250 word passage chunks from hundreds of raw candidate lines.
   - *Note*: Semantic relevance measures textual topic similarity (0–100%) and is strictly distinguished from verification confidence or truth probability.

4. **Real-World Visual Evidence Integration**:
   - Retrieves real web images via claim-aware BGE-M3 semantic relevance matching against textual metadata (titles, alt text).
   - Visual items serve as contextual visual evidence only and **never** influence the verdict, confidence score, or textual evidence set.

5. **Hugging Face Inference Integration**:
   - Powered by `huggingface_hub.InferenceClient` using models like `meta-llama/Llama-3.3-70B-Instruct`.
   - Includes a conservative heuristic fallback mode when primary LLM inference is unreachable or rate-limited.

---

## 🚦 Supported Verdict Types

The system outputs a structured, non-binary verdict from the following vocabulary:

| Verdict | Symbol | Description |
| :--- | :---: | :--- |
| **Supported** | 🟢 | Direct, reliable evidence from primary or secondary sources explicitly corroborates the core factual proposition. |
| **Contradicted** | 🔴 | Direct, reliable evidence explicitly refutes, denies, or proves facts incompatible with the claim. |
| **Insufficient Evidence** | 🟡 | Available retrieved evidence is incomplete, ambiguous, or lacks explicit facts to confirm or refute the claim. |
| **Conflicting Evidence** | 🟠 | High-credibility sources directly contradict one another or present conflicting empirical findings. |
| **Subjective / Opinion** | 🔵 | The statement is a value judgment, qualitative framing, or opinion that is not objectively verifiable. |

---

## 🔬 Evidence & Source Quality Principles

- **Exact Domain Matching**: Source tiering evaluates exact hostnames and subdomains. Unknown or unclassified domains default conservatively to secondary/low-confidence tiers.
- **Passage-Only Entailment**: LLM verification is instructed to evaluate logical entailment strictly against the text inside `Passage: "..."`. Article titles, domain names, and URLs serve provenance context only and are **not** treated as factual proof.
- **Evidence Quality Gate**: Candidate chunks undergo strict relevance filtering before entering LLM verification.
- **Duplicate & Snippet Filtering**: Deduplicates identical URLs and rejects near-duplicate passage chunks.

---

## 🛡️ Provenance, Safety & SSRF Protections

- **Strict Provenance Validation**: The system validates all LLM evidence references (`ev_1`, `ev_2`) against original retrieved `EvidenceItem` instances. Unrecognized or hallucinated citations are automatically rejected.
- **SSRF & Private Network Protection**: URL fetching validates target hostnames and blocks private, loopback, local, and metadata IP addresses (`127.0.0.1`, `localhost`, `10.x`, `172.16-31.x`, `192.168.x`, `169.254.x`, `::1`).
- **Subject-Page Evidence Isolation**: When analyzing a specific webpage, that webpage is treated as **context**, not independent proof. The exact URL and its canonical equivalent are filtered out of independent evidence retrieval while retaining same-domain independent articles.

---

## 🖥️ Frontend & User Interface

The React + Vite frontend features a clean 3-column dashboard:
- **Left Column**: Product overview and core architectural principles.
- **Center Column**: Main claim input form, verdict banner, explanation, visual evidence carousel/grid, evidence summary cards, and limitations.
- **Right Column**: Authoritative resource links (with tier badges) and key takeaways derived from evidence analysis.

*Metric Display Boundaries*:
- **Verification Confidence**: Displayed as a percentage representing verifier model confidence based on evidence quality and agreement.
- **Relevance**: Displayed as `% Relevance` (bounded to 0–100%) representing semantic passage similarity.

---

## 🔌 API Reference

### `POST /api/analyze`
Analyzes a claim, URL, or URL + Question string.

#### Request Payload
```json
{
  "claim": "Is India a state"
}
```

#### Response Structure (`AnalysisResult`)
```json
{
  "claim": "Is India a state",
  "claim_type": "factual",
  "verdict": "contradicted",
  "verdict_symbol": "🔴",
  "verdict_title": "Contradicted",
  "confidence_score": 0.8,
  "explanation": "The claim 'Is India a state' is contradicted by the evidence. Official sources specify that India is a sovereign federal union comprising 28 states and 8 union territories...",
  "supporting_evidence": [],
  "contradicting_evidence": [
    {
      "id": "ev_1",
      "url": "https://en.wikipedia.org/wiki/India",
      "title": "India - Wikipedia",
      "domain": "en.wikipedia.org",
      "source_tier": "secondary",
      "passage": "India, officially the Republic of India, is a country in South Asia...",
      "similarity_score": 0.68,
      "stance": "contradicts",
      "stance_explanation": "Directly establishes that India is a country containing states rather than a state itself."
    }
  ],
  "evidence_limitations": [
    "The evidence passages primarily utilize general geographic and administrative descriptions."
  ],
  "all_sources": [
    {
      "url": "https://en.wikipedia.org/wiki/India",
      "domain": "en.wikipedia.org",
      "title": "India - Wikipedia",
      "tier": "secondary",
      "tier_reason": "Reputable general reference encyclopedia"
    }
  ],
  "relevant_images": [],
  "latency_seconds": 12.45,
  "mode": "claim"
}
```

### `GET /api/health`
Returns system operational status and model readiness.

---

## 📁 Repository Structure

```
hackathon/
├── .env.example               # Environment variable configuration template
├── requirements.txt           # Backend Python dependencies
├── cli.py                     # Command-line interface for local verification testing
├── run_server.py              # FastAPI server launcher script
├── api/
│   ├── __init__.py
│   └── main.py                # FastAPI app & endpoint handlers (/api/analyze, /api/health)
├── core/
│   ├── __init__.py
│   ├── config.py              # Configuration manager & environment loading
│   ├── schemas.py             # Pydantic data contracts (AnalysisResult, EvidenceItem, etc.)
│   ├── claim_parser.py        # Step 1: Claim classification & search query formulation
│   ├── retriever.py           # Step 2: Web search retrieval & image search (DDGS)
│   ├── source_filter.py       # Step 3: Domain tiering (Primary, Secondary, Low-Confidence)
│   ├── extractor.py           # Step 4: Webpage fetching, HTML cleaning & passage chunking
│   ├── ranker.py              # Step 5: BGE-M3 semantic similarity evidence ranking
│   ├── evidence_gate.py       # Step 5.5: Evidence Quality Gate filtering
│   ├── verifier.py            # Step 6: Hugging Face LLM comparative analysis & fallback
│   ├── pipeline.py            # Step 7: End-to-end pipeline orchestration
│   ├── url_normalizer.py      # URL normalization & equivalence comparison
│   ├── url_fetcher.py         # Webpage fetcher with SSRF protection & metadata extraction
│   └── url_pipeline.py        # Pipeline handler for URL & URL+Question input modes
├── frontend/                  # React + TypeScript + Vite frontend web application
│   ├── src/
│   │   ├── components/        # ClaimInput, ResultCard, LeftSidebar, RightSidebar
│   │   ├── types.ts           # Frontend TypeScript data interfaces
│   │   ├── api.ts             # API client fetching logic
│   │   ├── App.tsx            # Main dashboard component
│   │   └── index.css          # Vanilla CSS styling & design system
│   ├── package.json
│   └── vite.config.ts
└── tests/                     # Unit test suite (101 backend tests)
    ├── test_parser.py
    ├── test_source_filter.py
    ├── test_pipeline.py
    ├── test_verifier.py
    ├── test_evidence_gate.py
    ├── test_api.py
    ├── test_url_verification.py
    ├── test_relevance_and_caveats.py
    └── test_image_relevance.py
```

---

## 🛠️ Local Setup & Installation

### 1. Backend Environment Setup
Ensure Python 3.10+ is installed.

```bash
# Clone the repository and create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Set your Hugging Face Access Token in `.env`:
```env
HF_TOKEN=your_huggingface_token_here
HF_LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct
HF_EMBEDDING_MODEL=BAAI/bge-m3
```

### 3. Run Backend Server
```bash
python run_server.py
```
The backend API will start at `http://localhost:8000`. Interactive documentation is available at `http://localhost:8000/docs`.

### 4. Run Frontend Application
In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173` to access the web application.

---

## 🧪 Testing & Build Verification

### Backend Unit Test Suite
Execute the full backend unit test suite (101 tests):

```bash
python -m unittest discover -s tests
```

### Frontend Production Build
Validate TypeScript compilation and build production assets:

```bash
cd frontend
npm run build
```

---

## 🔒 Security & Trust Boundaries

- **Untrusted Web Content**: All retrieved web text and external webpages are treated as untrusted data and sanitized before HTML parsing.
- **LLM Safety Gate**: LLM output is validated through Pydantic schemas and provenance checks before being accepted.
- **SSRF Guards**: Restricts URL fetching from attempting to contact local loopback or internal RFC1918 networks.
- **Environment Secrets**: API keys (`HF_TOKEN`) are loaded from `.env` and never committed or exposed in client responses.

---

## 🏛️ Design Principles & Boundaries

- **Evidence First**: Decisions depend on verifiable evidence passages rather than ungrounded model weights.
- **Conservative Fallback**: Prefers `insufficient_evidence` when evidence is incomplete or unreachable.
- **Distinct Metrics**: Semantic relevance (`% Relevance`) measure topical similarity; `Confidence Score` measures verdict certainty based on evidence authority.
- **Contextual Visuals**: Images illustrate topics visually and never determine factual verdicts.