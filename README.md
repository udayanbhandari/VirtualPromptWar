# ClauseWise — AI for Legal Assistance & Access

ClauseWise is an AI-powered legal document intelligence platform that parses complex contracts, flags intra-document inconsistencies, assesses clause-level risk with Indian statutory grounding, performs side-by-side contract comparison, provides strictly grounded document Q&A, and generates structured lawyer-consultation briefs.

---

## 🏛️ GenAI Architecture — Explicit Mapping

The following table explicitly maps every pipeline stage in ClauseWise to the specific Gemini model and GenAI capability utilized:

| Pipeline Component | GenAI Capability / API Feature | Gemini Model | Pipeline Location & Purpose |
|---|---|---|---|
| **Document Ingestion** | Multimodal Document Understanding (`Part.from_bytes`) | `gemini-2.5-flash` | `/api/ingest/` — Ingests raw PDFs, images, and scanned contracts without OCR pre-processing. |
| **Clause Extraction & Inconsistencies** | Structured Output JSON Schema (`response_schema`, `response_mime_type`) | `gemini-2.5-flash` | `/api/ingest/` & `/api/clauses/{id}` — Parses text into typed `Clause` objects, classifies risk, and detects intra-document contradictions. |
| **Statute RAG Retrieval** | Dense Vector Embeddings (`embed_content`) | `text-embedding-004` | `app/services/vector_store.py` — Embeds Indian statutes (Contract Act, Consumer Protection, DPDP) and contractual clauses into ChromaDB for semantic retrieval. |
| **Statute Grounding & Risk Enrichment** | Controlled Few-Shot Grounding & Constraint Reasoning | `gemini-2.5-flash` | `app/services/gemini_client.py` — Evaluates candidate retrieved statutory sections against flagged clauses; enriches risk rationales without forcing false citations. |
| **Document Comparison & Risk Delta** | Comparative Semantic Alignment & Structured Evaluation | `gemini-2.5-flash` | `/api/compare/` — Matches clauses across two contract versions, evaluates favorability, and computes user risk delta. |
| **Bounded Document Q&A** | Grounded System Prompting with Strict Negative Constraints | `gemini-2.5-flash` | `/api/ask/` — Answers questions strictly scoped to document clauses and statutes; explicitly declines out-of-scope queries with varied disclaimers. |
| **Next Steps & Consultation Brief** | Structured Action Synthesis & Executive Summarization | `gemini-2.5-flash` | `/api/nextsteps/{id}` — Generates concrete personal checklists, verbatim lawyer consultation questions, and exportable briefs. |

---

## 🛠️ Technology Stack

- **AI Engine & Embeddings:** Google GenAI SDK (`gemini-2.5-flash`, `text-embedding-004`)
- **Backend:** FastAPI (Python 3.11+) + Pydantic v2 + PyMuPDF / FPDF2
- **Vector Database:** ChromaDB (Local persistent & in-memory vector store)
- **Frontend:** React 19 + TypeScript + Vite + TailwindCSS v4
- **Testing & Resilience:** Pytest + AsyncIO + Exponential Backoff Retry Client

---

## 📁 Repository Structure

```text
Virtualprompt/
├── docker-compose.yml          # Orchestrates backend, frontend, and ChromaDB
├── README.md                   # Submission documentation & architecture mapping
├── SETUP.md                    # Step-by-step installation & environment configuration
├── DEMO.md                     # 2-3 minute rehearsed live demo script
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint, CORS, route mounting
│   │   ├── routes/             # Feature API endpoints
│   │   │   ├── ingest.py       # POST /api/ingest/ (multimodal PDF upload & extraction)
│   │   │   ├── clauses.py      # GET  /api/clauses/{doc_id} (clause risk & conflicts)
│   │   │   ├── compare.py      # POST /api/compare/ (two-document clause comparison)
│   │   │   ├── ask.py          # POST /api/ask/ (grounded document & statute Q&A)
│   │   │   └── nextsteps.py    # POST /api/nextsteps/ (action checklists & lawyer briefs)
│   │   ├── services/           # GenAI & indexing core services
│   │   │   ├── gemini_client.py# Google GenAI SDK wrapper (extraction, grounding, embeddings)
│   │   │   ├── vector_store.py # ChromaDB index of Indian legal statutes
│   │   │   ├── comparator.py   # Clause alignment and diff analysis
│   │   │   ├── document_qa.py  # Strictly bounded Q&A engine
│   │   │   ├── next_steps_generator.py # Consultation brief generator
│   │   │   └── document_store.py # Thread-safe document session store
│   │   └── models/
│   │       └── schemas.py      # Pydantic schemas (typed API contracts)
│   ├── fixtures/               # Sample contracts (rental, consulting, NDA, loan)
│   └── tests/                  # 26 automated integration & unit tests
│
└── frontend/                   # React + TypeScript + TailwindCSS application
    └── src/
        ├── App.tsx             # Root application shell & navigation
        ├── index.css           # Design tokens, typography & dark theme base
        ├── api/                # Resilient typed API client with retries
        ├── components/         # Reusable UI components (Navbar, RiskBadge, ClauseCard)
        └── pages/              # Core views (Upload, Clauses, Compare, Ask, NextSteps)
```

---

## 🚀 Quickstart

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Set GEMINI_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```

Backend endpoints:
- API Base: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend application: `http://localhost:5173`

---

## 🧪 Testing

Run the full automated test suite (unit tests, RAG grounding, route validation, and integration tests):

```bash
pytest backend/tests/ -v -o asyncio_mode=auto
```

All 26 tests pass across all failure modes and pipeline paths.

---

## 🗺️ Product Roadmap

While ClauseWise delivers deep end-to-end contract intelligence, the platform is architected for extensible modular growth. Our immediate post-hackathon roadmap focuses on two high-impact accessibility frontiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ClauseWise Future Roadmap                       │
├──────────────────────────────────┬─────────────────────────────────────┤
│ 🎙️ Phase A: Voice Accessibility  │ 🌐 Phase B: Multilingual Indic Law   │
│ • Real-time Speech-to-Text Q&A   │ • Multilingual Indian Contract Hub  │
│ • Audio consultation briefings   │ • Regional language summaries       │
│ • Low-literacy vocal walkthroughs│ • Cross-lingual statutory grounding │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### 1. Voice Accessibility & Multimodal Audio (`Gemini Live / Audio API`)
- **Vocal Contract Walkthroughs:** Enable audio summaries of complex clauses for visually impaired or low-literacy users, allowing users to listen to plain-language breakdowns.
- **Hands-Free Legal Q&A:** Voice-activated conversational interface using Gemini's native audio understanding to query documents verbally during live contract reviews.
- **Audio Consultation Debriefing:** Audio export of the "Questions for Your Lawyer" brief formatted for playback immediately prior to entering a consultation.

### 2. Vernacular & Indic Language Support (`Gemini Multilingual`)
- **Regional Indian Language Translation:** Automated plain-language translation into major Indic languages (Hindi, Tamil, Telugu, Kannada, Marathi, Bengali) to democratize legal access for non-English speakers.
- **Cross-Lingual Statutory Grounding:** Capability to query English statutes using regional language prompts, bridging the comprehension gap for vernacular contract signatories.
- **Vernacular Document Ingestion:** Multimodal OCR and clause parsing for bilingual state-level stamp papers and regional lease deeds.
