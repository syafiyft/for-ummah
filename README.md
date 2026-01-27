# 🌙 Agent Deen | وكيل الدين

**Trilingual AI Shariah Chatbot for Islamic Finance**

✨ Ask questions in **Arabic (العربية)**, **English**, or **Bahasa Melayu**

Powered by **Ollama** (Free & Local) or **Claude Haiku** (High Quality) with RAG from authoritative Shariah sources.

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.11+ | Required |
| **Ollama** | Latest | For local LLM inference |
| **Pinecone** | Free tier | For vector database |
| **Supabase** | Free tier | For PostgreSQL + Storage |

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd for-ummah

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

**Dependencies include:**

- `fastapi`, `uvicorn` - Backend API
- `streamlit` - Web UI
- `pinecone` - Vector database
- `pymupdf` - PDF text extraction
- `playwright` - Web scraping with WAF bypass
- `requests`, `beautifulsoup4` - Web scraping

### 3. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - Download from https://ollama.com
```

**Pull required models:**

```bash
# Start Ollama service
ollama serve

# In another terminal, pull models
ollama pull llama3.2           # Main LLM for chat
ollama pull nomic-embed-text   # Embeddings for RAG
```

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your Pinecone API key
```

**Required `.env` variables:**

```env
# Pinecone (required for vector DB)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX=shariah-kb

# Supabase (required for database + storage)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-supabase-key

# Optional Auth (Required only for Claude)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional settings
DATA_DIR=data
LOG_LEVEL=INFO

# Optional RAG tuning
RAG_RELEVANCE_THRESHOLD=0.60  # Min relevance score (0.60-0.70)
RAG_RERANK_TOP_K=25           # After reranking
```

> **Note:** Ollama runs 100% locally for free. An Anthropic API key is only needed if you want to use the Claude Haiku model.

### 5. Run the Application

**Terminal 1 - Ollama (must be running):**

```bash
ollama serve
```

**Terminal 2 - API Backend:**

```bash
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 3 - Streamlit UI:**

```bash
streamlit run app.py
```

**Access:**

- 🌐 **Streamlit UI:** <http://localhost:8501>
- 🔧 **API Docs:** <http://localhost:8000/docs>

---

## 📁 Project Structure

```
for-ummah/
├── app.py                  # Streamlit web UI
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
│
├── src/
│   ├── core/              # Configuration, language detection
│   ├── db/                # Supabase integration
│   │   ├── client.py      # Supabase client singleton
│   │   ├── models.py      # Pydantic data models
│   │   ├── storage.py     # Storage service (PDFs)
│   │   └── repositories/  # Database repositories
│   │       ├── documents.py   # Document CRUD
│   │       ├── chat.py        # Chat sessions/messages
│   │       ├── ingestion.py   # Ingestion history
│   │       └── job_status.py  # Background job status
│   ├── scrapers/          # Web scrapers (BNM, SC Malaysia)
│   ├── processors/        # PDF extraction, text chunking
│   ├── vector_db/         # Pinecone + Ollama embeddings
│   ├── ai/                # RAG pipeline, prompts, Ollama + Claude LLMs
│   ├── services/          # Business logic
│   │   ├── chat.py        # ChatService orchestrator
│   │   ├── history.py     # Chat history (Supabase)
│   │   └── ingestion.py   # Document ingestion pipeline
│   └── api/               # FastAPI endpoints
│
├── scripts/
│   ├── reindex_with_pages.py  # Re-process PDFs with page tracking
│   ├── scrape_url.py          # Download & index PDF from URL
│   └── translate_claude.py    # (Optional) Batch translation tool
│
├── docs/
│   └── architecture.md    # System architecture diagrams
│
└── data/                  # Local cache (primary storage in Supabase)
```

---

## 🛠️ Tech Stack

| Component | Technology | Cost |
|-----------|------------|------|
| **LLM (Local)** | Ollama llama3.2 | FREE (local) |
| **LLM (Cloud)** | Claude 3.5 Haiku | ~$0.001/query (High Quality) |
| **Embeddings** | Ollama nomic-embed-text | FREE (local) |
| **Vector DB** | Pinecone | Free tier |
| **Database** | Supabase PostgreSQL | Free tier |
| **Storage** | Supabase Storage | Free tier |
| **Backend** | FastAPI | - |
| **Frontend** | Streamlit | - |
| **PDF Extraction** | PyMuPDF → Tesseract OCR (cascade) | FREE |
| **Reranking** | CrossEncoder (ms-marco-MiniLM) | FREE |

---

## ✨ Features

- 🌍 **Trilingual:** Arabic (العربية), English, Bahasa Melayu
- 📚 **Authoritative Sources:** BNM, AAOIFI, SC Malaysia, JAKIM
- 🤖 **Hybrid AI:** Choose between **Ollama (Free)** or **Claude Haiku (Smart)**
- 🎯 **High-Precision Reranking:** CrossEncoder model boosts search relevance
- 🔄 **Query Translation:** Auto-translates Malay/Arabic queries to English for better search precision
- 📄 **Smart PDF:** Page-level tracking with Arabic OCR support
- 🔍 **Source Verification:** Clickable citations with **Exact Quote**, **Page Previews (Image)**, & **Highlighted Text**
- 💬 **Chat History:** Persistent conversation sessions stored in Supabase
- 📤 **Source Management:** Upload PDFs or add by URL directly in UI
- 🤖 **Automated Updates:** Scheduled background scraper (APScheduler) checks for new BNM/SC documents
- 📊 **Admin Dashboard:** Monitor document counts, storage, system health, and trigger manual updates
- ☁️ **Cloud Storage:** All documents stored in Supabase Storage with secure access

---

## 📦 Indexing Documents

### Re-index all PDFs

```bash
# Process all PDFs and index with page tracking
python scripts/reindex_with_pages.py
```

### Add a single PDF from URL

```bash
# Download and index a PDF directly from URL
python scripts/scrape_url.py "https://example.com/document.pdf"

# With custom title and source
python scripts/scrape_url.py "URL" --title "Custom Title" --source BNM
```

This will:

1. Extract text from PDFs with sentence-based chunking
2. Preserve page numbers for source citations
3. Upload to Pinecone with metadata

---

## 🧪 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat endpoint |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |
| `/history/chats` | GET | List all chat sessions |
| `/history/chat/{id}` | GET | Get specific chat session |
| `/history/chat` | POST | Create/update chat session |
| `/history/sources` | GET | List all indexed sources |
| `/ingest/url` | POST | Ingest document from URL |
| `/ingest/upload` | POST | Upload and ingest PDF |
| `/pdf/{source}/{filename}` | GET | Serve PDF file |
| `/pdf/list` | GET | List available PDFs |
| `/admin/trigger-update` | POST | Trigger scraper update |
| `/admin/job-status` | GET | Get background job status |

**Example API call:**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Murabaha?", 
    "language": "en",
    "model": "claude" 
  }'
```

---

## 🔧 Troubleshooting

### Ollama not connecting

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Pinecone connection issues

- Verify your API key in `.env`
- Check index name matches `PINECONE_INDEX`
- Ensure index exists in Pinecone dashboard

### PDF extraction problems

- Digital PDFs: Handled by PyMuPDF
- Scanned PDFs: Requires Tesseract OCR

```bash
# Install Tesseract (optional for scanned PDFs)
# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt install tesseract-ocr tesseract-ocr-ara
```

---

## 📄 License

Built for the Ummah 🌙

---

## 📞 Support

For questions or contributions, please open an issue on GitHub.
