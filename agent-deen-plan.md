# Agent Deen - Trilingual AI Shariah Chatbot

**Goal:** Build an AI chatbot for Islamic finance queries in Arabic, English, and Malay.

---

## ✅ Completed Features

| Feature | Status | Details |
|---------|--------|---------|
| **Project Setup** | ✅ Done | Clean architecture in `src/` |
| **PDF Scraping** | ✅ Done | BNM, AAOIFI scrapers with cascade extraction |
| **Text Chunking** | ✅ Done | Smart chunking with page tracking |
| **Vector DB** | ✅ Done | Pinecone + Ollama embeddings (FREE) |
| **RAG Pipeline** | ✅ Done | Ollama llama3.2 for chat (100% FREE) |
| **API Backend** | ✅ Done | FastAPI at port 8000 |
| **Streamlit UI** | ✅ Done | Trilingual interface with source display |
| **Language Detection** | ✅ Done | Arabic/English/Malay auto-detect |
| **Page Number Tracking** | ✅ Done | Chunks include source page numbers |
| **Re-indexing Script** | ✅ Done | `scripts/reindex_with_pages.py` created |
| **Source Citations** | ✅ Done | Displays source, file, and page number |

---

## 🔄 Pending Tasks (Future Updates)

### 🔴 High Priority

| Task | Notes |
|------|-------|
| **Page format: X/Total** | Show page as "Page 139/188" instead of just "Page 139" to handle PDF vs printed page numbering differences |
| **Multiple source citation** | When answer comes from multiple sources, list all of them in the answer section |
| **Reduce hallucination** | Improve prompt to ensure AI only answers from Shariah sources, not from its general knowledge |
| **Stricter source grounding** | Make the LLM quote directly from sources rather than paraphrasing with additional info |

### 🟡 Medium Priority

| Task | Notes |
|------|-------|
| **Add more sources** | SC Malaysia, JAKIM fatwas |
| **Source deduplication** | Better deduplication of overlapping chunks |
| **Confidence scoring** | Improve confidence calculation based on source relevance |

### 🟢 Low Priority

| Task | Notes |
|------|-------|
| **UI improvements** | Better mobile responsiveness |
| **Export answers** | Save Q&A to PDF |
| **Chat history** | Conversation context |

---

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

---

## Tech Stack (100% FREE)

| Component | Technology |
|-----------|------------|
| **LLM** | Ollama llama3.2 (LOCAL & FREE) |
| **Embeddings** | Ollama nomic-embed-text (LOCAL & FREE) |
| **Vector DB** | Pinecone (free tier) |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **PDF Extraction** | PyMuPDF → Tesseract (cascade) |

---

## Recent Changes (2026-01-20)

### Page Number Tracking

- `ExtractionResult.page_texts` - List of (page_num, text) tuples
- `TextChunk.page_number` - Source page number for each chunk
- `chunk_with_pages()` - Page-aware chunking function
- `scripts/reindex_with_pages.py` - Re-indexing script created

### Ollama Integration

- `src/ai/ollama_llm.py` - Local LLM client
- Replaced Anthropic Claude → Ollama llama3.2
- 100% free, runs locally

### UI Updates

- Source cards now display page numbers
- Confidence indicator added
- RTL Arabic text support

---

## Improvements Needed

### 1. Page Format Enhancement

**Current:** `Page 139`
**Target:** `Page 139/188`

Update these files:

- `src/processors/pdf_extractor.py` - Track total pages in `ExtractionResult`
- `src/processors/chunker.py` - Include total pages in `TextChunk` metadata
- `src/ai/rag.py` - Pass total pages to source display
- `app.py` - Display as "Page X/Total"

### 2. Multiple Source Citation

**Problem:** Answer only shows one source even when derived from multiple
**Solution:** Update prompt and answer formatting to list all relevant sources

### 3. Reduce Hallucination

**Problem:** LLM adds general knowledge not from Shariah sources
**Current prompt** has anti-hallucination instructions but needs strengthening

Improvements needed in `src/ai/prompts.py`:

```
- Add: "If information is not in the context, say so clearly"
- Add: "DO NOT add information from your training data"
- Add: "Quote directly from sources when possible"
- Add: "Start answer with 'Based on [Source]...'"
```

---

## Run Commands

```bash
# Install
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Pull models (first time only)
ollama pull llama3.2
ollama pull nomic-embed-text

# Run API
uvicorn src.api.main:app --reload --port 8000

# Run Streamlit UI (in separate terminal)
streamlit run app.py
```

---

## Environment (.env)

```env
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=shariah-kb
```

**No Anthropic/OpenAI keys needed!** 🎉

---

## Next Steps (Priority Order)

1. [ ] Implement page X/Total format in PDF extractor & UI
2. [ ] Update prompt to reduce hallucination (stricter source grounding)
3. [ ] Add multiple source citation support in answers
4. [ ] Add more Shariah documents (SC Malaysia, JAKIM)
5. [ ] Test with diverse Islamic finance queries
