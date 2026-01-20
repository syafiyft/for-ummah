# Agent Deen - Trilingual AI Shariah Chatbot

## Quick Start

**Goal:** Build an AI chatbot for Islamic finance queries in Arabic, English, and Malay.

## ✅ Completed Features

| Feature | Status | Details |
|---------|--------|---------|
| **Project Setup** | ✅ Done | Clean architecture in `src/` |
| **PDF Scraping** | ✅ Done | BNM, AAOIFI scrapers with cascade extraction |
| **Text Chunking** | ✅ Done | Smart chunking with page tracking |
| **Vector DB** | ✅ Done | Pinecone + Ollama embeddings (FREE) |
| **RAG Pipeline** | ✅ Done | Ollama llama3.2 for chat (100% FREE) |
| **API Backend** | ✅ Done | FastAPI at port 8000 |
| **Streamlit UI** | ✅ Done | Trilingual interface |
| **Language Detection** | ✅ Done | Arabic/English/Malay auto-detect |
| **Page Number Tracking** | ✅ Done | Chunks include source page numbers |

## 🔄 Pending Tasks

| Task | Priority | Notes |
|------|----------|-------|
| **Re-process PDFs** | 🔴 High | Need to re-run chunking with new page tracking |
| **Re-index to Pinecone** | 🔴 High | Upload new chunks with page numbers |
| **Add more sources** | 🟡 Medium | SC Malaysia, JAKIM fatwas |
| **Improve UI styling** | 🟢 Low | Optional enhancements |

## Architecture

```
src/
├── core/           # Configuration, enums, exceptions
├── scrapers/       # Base class + source-specific scrapers
├── processors/     # PDF extraction (with page tracking), chunking
├── vector_db/      # Pinecone + Ollama embeddings (FREE)
├── ai/             # RAG pipeline + Ollama LLM (FREE)
├── services/       # ChatService orchestrator
└── api/            # FastAPI endpoints
```

## Tech Stack (Updated - 100% FREE)

| Component | Technology |
|-----------|------------|
| **LLM** | Ollama llama3.2 (LOCAL & FREE) |
| **Embeddings** | Ollama nomic-embed-text (LOCAL & FREE) |
| **Vector DB** | Pinecone (free tier) |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **PDF Extraction** | PyMuPDF → Tesseract (cascade) |

---

## Recent Changes

### Page Number Tracking (Added)

- `ExtractionResult.page_texts` - List of (page_num, text) tuples
- `TextChunk.page_number` - Source page number for each chunk
- `chunk_with_pages()` - New function for page-aware chunking

### Ollama Integration (Added)

- `src/ai/ollama_llm.py` - Local LLM client
- Replaced Anthropic Claude → Ollama llama3.2
- 100% free, runs locally

---

## Run Commands

```bash
# Install
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Run API
uvicorn src.api.main:app --reload

# Run Streamlit UI
streamlit run app.py
```

## Environment (.env)

```
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=shariah-kb
```

**No Anthropic/OpenAI keys needed!** 🎉
