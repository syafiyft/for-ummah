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
| **Page X/Total Format** | ✅ Done | Shows "Page 8/24" in sources |
| **URL Scraper** | ✅ Done | `scripts/scrape_url.py` - download from direct URL |
| **Scope Detection** | ✅ Done | Rejects off-topic questions |
| **Anti-Hallucination Prompt** | ✅ Done | Stricter source grounding |
| **Sentence-Based Chunking** | ✅ Done | Clean chunks with full sentences, no broken words |

---

## 🔄 Pending Tasks (Future Updates)

### 🔴 High Priority

| Task | Notes |
|------|-------|
| **Better LLM Model** | Consider GPT-4 or Claude for better instruction following (current llama3.2 sometimes ignores prompt rules) |
| **Relevance Score Threshold** | Skip sources with low relevance score to avoid unrelated context |
| **Multiple source citation** | When answer comes from multiple sources, list all of them in the answer section |

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
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (first time only)
playwright install chromium

# Ensure Ollama is running
ollama serve

# Pull models (first time only)
ollama pull llama3.2
ollama pull nomic-embed-text

# Run API
uvicorn src.api.main:app --reload --port 8000

# Run Streamlit UI (in separate terminal)
streamlit run app.py

# Run BNM scraper (optional - to download new documents)
python -m src.scrapers.bnm
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
