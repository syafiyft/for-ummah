# Agent Deen System Architecture

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (Streamlit)"]
        UI[app.py]
        Chat[Chat Page]
        Sources[Manage Sources]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API[API Endpoints]
        ChatSvc[ChatService]
        IngestSvc[IngestionService]
        RAG[RAG Pipeline]
    end

    subgraph AI["🤖 AI Layer"]
        Ollama[Ollama LLM]
        Claude[Claude Haiku]
        Translator[Language Translator]
    end

    subgraph Storage["💾 Storage"]
        Pinecone[(Pinecone Vector DB)]
        PDFs[("data/ PDFs")]
    end

    subgraph Scrapers["🔧 Scrapers"]
        BNM[BNM Scraper]
        Manual[Manual Scraper]
        Playwright[Playwright WAF Bypass]
    end

    UI --> API
    Chat --> ChatSvc
    Sources --> IngestSvc
    
    ChatSvc --> RAG
    RAG --> Pinecone
    RAG --> Ollama
    RAG --> Claude
    RAG --> Translator
    
    IngestSvc --> Manual
    Manual --> Playwright
    Manual --> PDFs
    IngestSvc --> Pinecone
    
    API --> PDFs
```

## Data Flow: Ask a Question

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit
    participant A as FastAPI
    participant R as RAG Pipeline
    participant P as Pinecone
    participant L as LLM (Ollama/Claude)

    U->>S: Ask question in Malay
    S->>A: POST /chat
    A->>R: query(question)
    R->>R: Detect language (Malay)
    R->>R: Translate to English
    R->>P: Search similar chunks
    P-->>R: Top 5 chunks + metadata
    R->>R: Filter by relevance (>0.65)
    R->>L: Generate answer with context
    L-->>R: Answer in Malay
    R->>R: Ensure language (translate if needed)
    R-->>A: RAGResponse
    A-->>S: JSON response
    S-->>U: Display answer + sources
```

## Data Flow: Ingest Document

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit
    participant A as FastAPI
    participant I as IngestionService
    participant SC as ManualScraper
    participant PW as Playwright
    participant PR as PDF Processor
    participant P as Pinecone

    U->>S: Provide URL or Upload PDF
    S->>A: POST /ingest/url or /ingest/upload
    A->>I: ingest_from_url() or ingest_file()
    
    alt URL Ingestion
        I->>SC: scrape_from_url()
        SC->>PW: Download PDF (WAF bypass)
        PW-->>SC: PDF bytes
        SC->>SC: Save to data/manual/
    else File Upload
        I->>I: Save to data/manual/
    end
    
    I->>PR: extract_text()
    PR-->>I: Text + page numbers
    I->>I: chunk_with_pages()
    I->>I: Generate embeddings (Ollama)
    I->>P: Upsert vectors + metadata
    P-->>I: Success
    I-->>A: {status, pages, chunks}
    A-->>S: JSON response
    S-->>U: Success message
```

## Storage Structure

```
for-ummah/
├── data/
│   ├── bnm/                    # BNM scraped PDFs
│   │   └── *.pdf
│   ├── manual/                 # User uploads & URL downloads
│   │   └── *.pdf
│   └── processed/
│       └── all_chunks_with_pages.json  # Local backup
│
├── src/
│   ├── api/main.py             # FastAPI endpoints
│   ├── services/
│   │   ├── __init__.py         # ChatService
│   │   └── ingestion.py        # IngestionService
│   ├── ai/
│   │   ├── rag.py              # RAG Pipeline
│   │   ├── ollama_llm.py       # Ollama client
│   │   ├── claude_llm.py       # Claude client
│   │   └── translator.py       # Language enforcement
│   ├── scrapers/
│   │   ├── base.py             # BaseScraper + Playwright
│   │   ├── bnm.py              # BNM website scraper
│   │   └── manual.py           # User upload scraper
│   ├── processors/
│   │   ├── pdf.py              # Text extraction
│   │   └── chunker.py          # Sentence-based chunking
│   └── vector_db/
│       └── pinecone.py         # Pinecone client
│
└── app.py                      # Streamlit frontend
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Ask a question, get RAG answer |
| `/ingest/url` | POST | Ingest document from URL |
| `/ingest/upload` | POST | Upload and ingest PDF |
| `/pdf/{source}/{filename}` | GET | Serve PDF for viewer |
| `/pdf/list` | GET | List all available PDFs |
| `/health` | GET | Health check |

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **RAG Pipeline** | `src/ai/rag.py` | Orchestrates search + LLM |
| **Ingestion** | `src/services/ingestion.py` | PDF processing pipeline |
| **PDF Viewer** | `src/api/main.py` | Serves PDFs with page navigation |
| **Playwright** | `src/scrapers/base.py` | WAF bypass for downloads |
