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
| **Chat History** | ✅ Done | Sidebar with session list, persistent storage |
| **Page Number Tracking** | ✅ Done | Chunks include source page numbers |
| **Re-indexing Script** | ✅ Done | `scripts/reindex_with_pages.py` created |
| **Source Citations** | ✅ Done | Displays source, file, and page number |
| **Page X/Total Format** | ✅ Done | Shows "Page 8/24" in sources |
| **URL Scraper** | ✅ Done | `scripts/scrape_url.py` - download from direct URL |
| **Scope Detection** | ✅ Done | Rejects off-topic questions |
| **Anti-Hallucination Prompt** | ✅ Done | Stricter source grounding |
| **Sentence-Based Chunking** | ✅ Done | Clean chunks with full sentences, no broken words |
| **Language Response Fix** | ✅ Done | Translation fallback ensures correct response language |

---

## 🔄 Pending Tasks (Future Updates)

### 🔴 High Priority

| Task | Notes |
|------|-------|
| **Better LLM Model** | Consider GPT-4 or Claude for better instruction following (current llama3.2 sometimes ignores prompt rules) |
| ~~**Relevance Score Threshold**~~ | ✅ **COMPLETED** - Configurable via `rag_relevance_threshold` setting (default: 0.65) |
| ~~**Multiple source citation**~~ | ✅ **COMPLETED** - LLM prompt updated to require inline citations and "Sources:" footer |

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
| ~~**Chat history**~~ | ✅ **COMPLETED** - See 2026-01-22 changes |

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
| **Web Scraping** | Playwright (WAF bypass) + BeautifulSoup |

---

## Recent Changes (2026-01-20)

### Playwright Integration for WAF Bypass

- `src/scrapers/base.py` - Added Playwright support methods:
  - `_get_page_with_playwright()` - Fetch pages bypassing WAF
  - `_get_soup_with_playwright()` - Parse HTML with WAF bypass
  - `_download_pdf_with_playwright()` - Download PDFs through WAF
  - `_download_pdf_fallback()` - Fallback to requests if Playwright fails
- `src/scrapers/bnm.py` - Updated BNM scraper to use Playwright
  - Bypasses AWS WAF bot protection on BNM website
  - Falls back to requests if Playwright unavailable
  - Added policy page resolution for non-PDF links
- `requirements.txt` - Added `playwright>=1.40.0`
- Deleted standalone `scraper.py` (merged into `src/scrapers/`)

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

## Recent Changes (2026-01-21)

### URL Scraper (Direct Download)

- `src/scrapers/base.py` - New methods:
  - `scrape_from_url()` - Download PDF from direct URL
  - `_sanitize_title_from_url()` - Clean filename extraction
- `scripts/scrape_url.py` - NEW standalone script for URL-to-index pipeline
- Clean filenames (removes numeric IDs like `938039` from BNM URLs)

### Page X/Total Format

- `TextChunk.total_pages` - Added to chunker
- `app.py` - Now displays "Page 8/24" instead of just "Page 8"

### Anti-Hallucination & Scope Detection

- `src/ai/prompts.py` - Major improvements:
  - STEP 0: Scope detection (reject off-topic questions)
  - Stricter context relevance checking
  - Require source attribution at start
  - Better "I don't know" responses
- `app.py` - Hide irrelevant sources for out-of-scope questions
- Chatbot now politely declines non-Islamic finance questions

### Sentence-Based Chunking

- `src/processors/chunker.py` - Completely rewritten:
  - `_clean_chunk_start()` - Removes partial sentences from chunk beginnings
  - Chunks now end at sentence boundaries (. ! ? etc.)
  - Smart overlap handling - next chunk starts at sentence beginning
  - No more broken words like "e, including where–" at chunk starts
- Re-indexed all documents: 7600 cleaner chunks (down from 8503)

### Language Response Fix (2026-01-21)

- **Problem:** LLM (llama3.2) often responded in English even when asked in Malay
- **Solution:** Two-layer approach:
  1. Stronger prompt enforcement with explicit language rules
  2. Translation fallback using `langdetect` + `deep-translator`
- `src/ai/translator.py` - NEW module for language enforcement
- `src/ai/prompts.py` - Language instruction at START of prompt
- `src/ai/rag.py` - Integrated translator after LLM response
- `src/core/language.py` - Added more Malay markers for detection
- `requirements.txt` - Added `langdetect`, `deep-translator`

---

### Language & Model Updates (2026-01-21 Part 2)

- **Query-Time Translation**: ✅ Done. Malay/Arabic queries translated to English for better search precision.
- **Claude Haiku Integration**: ✅ Done. Added high-quality model option.
  - **Fix**: Resolved API key loading issue in `rag.py` to prevent silent fallback to Ollama.
  - **Verification**: Added `scripts/verify_claude.py` and UI badge.
- **Model Selector UI**: ✅ Done. Users can choose between "🆓 Ollama" and "⚡ Claude Haiku".
- **Strict Anti-Hallucination**: ✅ Done. Returns "not enough info" if no high-relevance chunks found.
- **Cleaner Source Display**: ✅ Done. Removed 12-char hex IDs from filenames in both Source Cards and LLM Context (e.g. `d5583ab...Debit Card` -> `Debit Card`).
- **Language Response Fix**: ✅ Done. `ensure_response_language` fallback ensures correct response language.
- **UI Improvements**: ✅ Done. Added "Model Used" badge (e.g., "Model: ⚡ Claude Haiku") to confirm active model.
- **Re-indexing**: ✅ Done (Partial). Re-indexed with 5 new BNM documents (Debit/Credit Cards) for testing.

## Future Enhancements (ToDo)

### 🔴 High Priority

| Task | Notes |
|------|-------|
| ~~**Full Re-scrape**~~ | ✅ **COMPLETED** - Removed `limit=5` from `src/scrapers/bnm.py`. Run `python -m src.scrapers.bnm` to scrape all. |
| ~~**Tune Relevance Threshold**~~ | ✅ **COMPLETED** - Now configurable via `rag_relevance_threshold` in settings (or `RAG_RELEVANCE_THRESHOLD` env var) |
| **Parallel Translation** | Implement async batch translation for faster indexing if needed. |

### 🟡 Medium Priority

| Task | Notes |
|------|-------|
| **Add more sources** | SC Malaysia, JAKIM fatwas |
| **Source deduplication** | Better deduplication of overlapping chunks |

### ✅ Chat History Feature - COMPLETED (2026-01-22)

The Chat History feature has been fully implemented with the following architecture:

1. **Storage Layer**:
    - API-based persistence via FastAPI endpoints
    - `src/services/history.py` - History service with JSON file storage
    - Structure: `session_id -> { title, created_at, messages: [] }`

2. **State Management**:
    - `st.session_state.current_session_id`: Tracks active conversation
    - `st.session_state.messages`: List of message objects

3. **UI Implementation**:
    - **Sidebar**:
        - "New Chat" button at top
        - Recent Chats list with session switching
        - Active chat highlighted with `#FF4B4B` (Streamlit red)
    - **Main Area**:
        - Full conversation display with `st.chat_message()`

4. **API Endpoints**:
    - `GET /history/chats` - List all chat sessions
    - `GET /history/chat/{id}` - Get specific chat session
    - `POST /history/chat` - Create/update chat session

5. **Files Modified**:
    - `app.py` - Chat history UI integration
    - `src/api/main.py` - History API endpoints
    - `src/services/history.py` - History service (NEW)

---

## Recent Changes (2026-01-22)

### Chat History Feature

- **Sidebar Navigation**: "New Chat" button + recent chats list with clickable session switching
- **Persistent Storage**: API-based history service with JSON file backend
- **UI Highlights**: Active chat highlighted with `#FF4B4B` (Streamlit red)
- **Files**:
  - `app.py` - Chat history UI integration
  - `src/api/main.py` - New endpoints: `GET /history/chats`, `GET /history/chat/{id}`, `POST /history/chat`
  - `src/services/history.py` - NEW history service

### Source Management UI (Upload & URL)

- `app.py` - Added **"Manage Sources"** page with:
  - **Add by URL**: Download PDFs from direct URLs (with WAF bypass via Playwright)
  - **Upload PDF**: Upload local PDFs for indexing
- `src/api/main.py` - New endpoints:
  - `POST /ingest/url` - Ingest document from URL
  - `POST /ingest/upload` - Ingest uploaded PDF file
- `src/services/ingestion.py` - NEW service for ingestion pipeline orchestration
- `src/scrapers/manual.py` - NEW scraper for user-submitted documents
- `requirements.txt` - Added `python-multipart` for file upload support

### Playwright Async Fix (Critical Bug Fix)

- **Problem:** Playwright sync API conflicted with FastAPI's asyncio loop, causing "Playwright Sync API inside asyncio loop" error
- **Solution:** Added `_download_with_playwright_sync()` helper in `src/scrapers/base.py`, runs in `ThreadPoolExecutor` to avoid blocking asyncio
- URL scraping now works correctly from the Streamlit UI

### Clickable Source Snippets with PDF Viewer

- `src/api/main.py` - New endpoints:
  - `GET /pdf/{source}/{filename}` - Serve PDFs from data directory with security checks
  - `GET /pdf/list` - List all available PDFs
- `src/ai/rag.py` - Added `filename` field to source response (original filename for PDF URL)
- `app.py` - Source cards are now **expandable**:
  - Click to expand and see snippet + "Open PDF in Browser" button
  - PDFs open in new tab at specific page (`#page=N` fragment)
  - Fallback for legacy chunks missing filename metadata
- Fuzzy filename matching in API for files with spaces/special chars

### High-Priority Task Completion

- **Full Re-scrape Ready**: Removed `limit=5` from `src/scrapers/bnm.py` (line 208)
  - Run `python -m src.scrapers.bnm` to scrape all BNM documents
- **Configurable Relevance Threshold**: Added `rag_relevance_threshold` to `src/core/config.py`
  - Default: 0.65 (tune via `.env` with `RAG_RELEVANCE_THRESHOLD=0.60`)
  - `src/ai/rag.py` now uses `settings.rag_relevance_threshold`
- **Multiple Source Citation**: Enhanced `src/ai/prompts.py` instruction #7
  - LLM now required to cite sources inline ("According to Source 1...")
  - LLM must add "Sources:" footer listing all sources used
  - Multilingual: "Sumber:" (Malay), "المصادر:" (Arabic)

---

## Completed Features (Updated 2026-01-22)

| Feature | Status | Details |
|---------|--------|---------|
| **Chat History** | ✅ Done | Sidebar with session list, persistent API storage |
| **Source Management UI** | ✅ Done | Upload PDF or Add by URL in Streamlit |
| **PDF Viewer** | ✅ Done | Click source snippet → open PDF at page |
| **Playwright Async Fix** | ✅ Done | ThreadPoolExecutor wrapper for FastAPI |
| **Full Re-scrape Ready** | ✅ Done | Removed `limit=5` from BNM scraper |
| **Configurable Relevance Threshold** | ✅ Done | `rag_relevance_threshold` in config (default 0.65) |
| **Multiple Source Citation** | ✅ Done | Enhanced prompt for inline + footer citations |

## Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Run API (backend)
uvicorn src.api.main:app --reload --port 8000

# Run Streamlit UI (frontend)
streamlit run app.py

# Run Claude Translation (optional - one time)
# python scripts/translate_claude.py
```

## Environment (.env)

```env
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=shariah-kb
ANTHROPIC_API_KEY=sk-ant-... (Optional - for Claude)
```
