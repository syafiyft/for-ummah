# Agent Deen - Technical Architecture Documentation

## Executive Summary

**Agent Deen** is a trilingual (Arabic/English/Malay) AI-powered Shariah compliance assistant with a sophisticated backend built on **FastAPI, Pinecone, and hybrid LLM support**.

### Key Technical Differentiators

| Feature | Implementation |
|---------|----------------|
| **Zero-Hallucination** | Source-grounded RAG with citation extraction |
| **Dual LLM** | FREE (Ollama local) + Premium (Claude Haiku) |
| **Intelligent Reranking** | CrossEncoder model for precision |
| **Multi-language** | Query translation for better semantic search |
| **Auto-Updates** | Background scraping with WAF bypass |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                        │
│            (Language/Model Selection, Chat UI)               │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                          │
│  /chat  /ingest/url  /history  /admin  /pdf/{source}/{file} │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                             │
│      ChatService → HistoryService → IngestionService        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                              │
│  Query → Translate → Embed → Search → Rerank → Generate     │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   OLLAMA     │    │   PINECONE   │    │    CLAUDE    │
│  (Local LLM) │    │ (Vector DB)  │    │  (Cloud LLM) │
│    FREE      │    │   FREE tier  │    │  ~$0.001/q   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## RAG Pipeline (4-Stage)

```
STAGE 1: QUERY PREPARATION
├── Detect language (Arabic/English/Malay)
├── Translate non-English → English (better search)
└── Rewrite with context (resolve "it", "that")

STAGE 2: HIGH-RECALL RETRIEVAL
├── Embed query → 768D vector (Ollama nomic-embed-text)
├── Pinecone search → top-60 candidates
└── Cast wide net for recall

STAGE 3: HIGH-PRECISION RERANKING  ⭐ Key Innovation
├── CrossEncoder model (ms-marco-MiniLM-L-6-v2)
├── Score all (query, document) pairs
├── Sort by relevance score
└── Select top-25 for context

STAGE 4: LLM GENERATION
├── Format context with source citations
├── Generate answer (Ollama or Claude)
├── Ensure response in target language
└── Extract sources with confidence score
```

---

## Document Ingestion Pipeline

```
PDF/URL Input
    ↓
EXTRACT (PyMuPDF → Tesseract OCR fallback)
    ↓
CHUNK (1000 chars, 200 overlap, sentence boundaries)
    ↓
EMBED (Ollama nomic-embed-text, 768D)
    ↓
INDEX (Pinecone with metadata: source, page, language)
```

**Metadata stored per chunk:**
- `source`: BNM, SC, AAOIFI, JAKIM, Manual
- `page_number` / `total_pages`
- `language`: en, ar, ms
- `original_text`: preserves source language

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Main Q&A endpoint |
| `/ingest/url` | POST | Index document from URL |
| `/ingest/upload` | POST | Index uploaded PDF |
| `/history/chats` | GET | List conversations |
| `/history/chat/{id}` | GET/DELETE | Manage session |
| `/admin/trigger-update` | POST | Manual scraper run |
| `/pdf/{source}/{file}` | GET | Serve PDF (secure) |

---

## Technology Stack

| Layer | Technology | Cost |
|-------|------------|------|
| **Frontend** | Streamlit | FREE |
| **API** | FastAPI + Uvicorn | FREE |
| **LLM (Local)** | Ollama llama3.2 | FREE |
| **LLM (Cloud)** | Claude 3.5 Haiku | ~$0.001/query |
| **Embeddings** | Ollama nomic-embed-text | FREE |
| **Reranking** | CrossEncoder (sentence-transformers) | FREE |
| **Vector DB** | Pinecone Serverless | FREE tier |
| **PDF Extraction** | PyMuPDF + Tesseract | FREE |
| **Web Scraping** | Playwright + BeautifulSoup | FREE |
| **Translation** | Google Translate (deep-translator) | FREE |
| **Scheduling** | APScheduler | FREE |

---

## Performance

| Metric | Ollama | Claude |
|--------|--------|--------|
| **End-to-end latency** | 4-10s | 2-5s |
| **Throughput** | ~6 q/min | ~30 q/min |
| **Cost per query** | $0 | ~$0.001 |

**Latency breakdown:**
- Query embedding: 500ms
- Vector search: 300ms
- Reranking (60 docs): 1-2s
- LLM generation: 2-5s (Ollama) / 1-2s (Claude)

---

## Security Features

- **Path traversal protection** on PDF serving
- **API key management** via `.env` (never in code)
- **Input validation** (length, types, allowed values)
- **CORS configuration** (restrict in production)

---

## Scaling Strategy

| Component | Current | Scaled |
|-----------|---------|--------|
| LLM | Single Ollama | Multiple instances / Claude API |
| Vector DB | Pinecone Serverless | Already scalable |
| Storage | Local filesystem | S3/GCS |
| Reranking | Single CPU | Distributed workers |

---

## Key Algorithms

### 1. Reranking (Precision Boost)

```python
reranker = CrossEncoder("ms-marco-MiniLM-L-6-v2")
scores = reranker.predict([(query, doc) for doc in candidates])
top_docs = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)[:25]
```

### 2. Language Detection

```python
arabic_ratio = arabic_chars / total_chars
if arabic_ratio > 0.6: return ARABIC
elif malay_markers >= 2: return MALAY
else: return ENGLISH
```

### 3. Query Rewriting (Context-Aware)

```
Input: "Tell me more about it"
History: [User asked about Murabaha]
Output: "What are the conditions and applications of Murabaha?"
```

---

## Anti-Hallucination Guardrails

1. **Source-grounded responses** - LLM can only cite retrieved documents
2. **Explicit citation format** - Every claim linked to source
3. **Confidence scoring** - Based on number of supporting documents
4. **Out-of-scope rejection** - Declines non-Islamic finance questions
5. **Knowledge gap admission** - Says "I don't have information" when appropriate

---

## Data Flow: Query Execution

```
┌─────────────────────────────────────────────────────────────┐
│ USER INTERACTION (Streamlit)                                │
│   → Select language/model → Enter question → Send           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ API LAYER (POST /chat)                                      │
│   → Validate input → Get ChatService → Load context         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SERVICE LAYER (ChatService)                                 │
│   → Detect language → Select LLM → Get RAG pipeline         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RAG PIPELINE                                                │
│   → Translate query → Embed → Search Pinecone               │
│   → Rerank with CrossEncoder → Generate with LLM            │
│   → Format sources → Return response                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE                                                    │
│   → Log to history → Return JSON → Display in UI            │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Document Ingestion

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: PDF Upload or URL                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EXTRACT                                                     │
│   → PyMuPDF (digital) or Tesseract OCR (scanned)           │
│   → Quality assessment (0.0 - 1.0)                         │
│   → Page-level text extraction                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ CHUNK                                                       │
│   → Split by sentence boundaries                            │
│   → Target: 1000 chars, Overlap: 200 chars                 │
│   → Attach metadata (source, page, language)               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ EMBED & INDEX                                               │
│   → Ollama embedding (768D vectors)                        │
│   → Batch upsert to Pinecone (50 vectors/batch)            │
│   → Store with full metadata                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RESULT                                                      │
│   → Log to ingestion_history.json                          │
│   → Return: status, chunks, pages, duration                │
└─────────────────────────────────────────────────────────────┘
```

---

## Background Job System

```
┌─────────────────────────────────────────────────────────────┐
│ SCHEDULER (APScheduler - 24h interval)                      │
│   OR manual trigger: POST /admin/trigger-update            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FOR EACH SOURCE (BNM, SC Malaysia)                          │
│   → Scrape website (Playwright for WAF bypass)             │
│   → Check ingestion history (skip duplicates)              │
│   → Download new PDFs                                       │
│   → Extract → Chunk → Index                                │
│   → Update progress (0.0 → 1.0)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ COMPLETION                                                  │
│   → Update job_status.json                                 │
│   → Log results                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
for-ummah/
├── app.py                      # Streamlit web UI
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
│
├── src/
│   ├── core/                   # Configuration, language detection
│   │   ├── config.py           # Pydantic settings
│   │   └── language.py         # Language detection
│   │
│   ├── api/                    # FastAPI endpoints
│   │   └── main.py             # All REST endpoints
│   │
│   ├── services/               # Business logic
│   │   ├── chat.py             # ChatService orchestrator
│   │   ├── history.py          # Conversation persistence
│   │   ├── ingestion.py        # Document processing
│   │   └── scheduler.py        # Background jobs
│   │
│   ├── ai/                     # AI/ML components
│   │   ├── rag.py              # RAG pipeline with reranking
│   │   ├── prompts.py          # LLM prompt templates
│   │   ├── translator.py       # Multi-language support
│   │   ├── ollama_llm.py       # Local LLM client
│   │   └── claude_llm.py       # Cloud LLM client
│   │
│   ├── vector_db/              # Vector storage
│   │   └── pinecone_store.py   # Pinecone + Ollama embeddings
│   │
│   ├── processors/             # Document processing
│   │   ├── pdf_extractor.py    # PyMuPDF + OCR
│   │   └── chunker.py          # Text chunking
│   │
│   └── scrapers/               # Web scrapers
│       ├── base.py             # Abstract base class
│       ├── bnm.py              # Bank Negara Malaysia
│       ├── sc.py               # Securities Commission
│       └── manual.py           # Direct URL handler
│
├── scripts/                    # Utility scripts
│   ├── reindex_with_pages.py   # Re-process all PDFs
│   └── scrape_url.py           # Index single URL
│
└── data/                       # Document storage
    ├── bnm/                    # BNM PDFs
    ├── sc_malaysia/            # SC PDFs
    ├── manual/                 # User uploads
    ├── chat_history.json       # Conversations
    ├── ingestion_history.json  # Ingestion logs
    └── job_status.json         # Background job state
```

---

## Environment Configuration

```bash
# .env file

# Required: Pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=shariah-kb

# Optional: Claude (for premium LLM)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Optional: RAG tuning
RAG_TOP_K=60
RAG_RERANK_TOP_K=25
RAG_RELEVANCE_THRESHOLD=0.60

# Optional: LLM settings
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2000
```

---

## External Service Dependencies

| Service | Purpose | Required | Cost |
|---------|---------|----------|------|
| **Ollama** | Local LLM + Embeddings | Yes | FREE |
| **Pinecone** | Vector database | Yes | FREE tier |
| **Anthropic** | Claude LLM | Optional | ~$0.001/query |
| **Google Translate** | Query/response translation | Auto | FREE tier |

---

## Deployment Options

### Development
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 3: Frontend
streamlit run app.py
```

### Production (Docker)
```dockerfile
# Recommended: Docker Compose with:
# - FastAPI container
# - Streamlit container
# - Ollama container (or use Claude API)
```

---

## Summary

Agent Deen delivers enterprise-grade Islamic finance Q&A with:

- **100% FREE local deployment** (Ollama + Pinecone free tier)
- **Premium option** (Claude Haiku at $0.001/query)
- **High precision** (CrossEncoder reranking)
- **Multi-language** (Arabic, English, Malay)
- **Auto-updating** knowledge base
- **Source verification** with page-level citations

Built for the Ummah.
