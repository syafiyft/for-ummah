# Agent Deen - Trilingual AI Shariah Chatbot

## Quick Start

**Goal:** Build an AI chatbot for Islamic finance queries in Arabic, English, and Malay.

## Architecture (Clean Code)

```
src/
├── core/           # Configuration, enums, exceptions
├── scrapers/       # Base class + source-specific scrapers
├── processors/     # PDF extraction, Arabic cleaning
├── vector_db/      # Pinecone integration
├── ai/             # RAG pipeline + prompts
├── services/       # ChatService orchestrator
└── api/            # FastAPI endpoints
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Claude 3.5 Sonnet |
| Embeddings | OpenAI text-embedding-3-large |
| Vector DB | Pinecone |
| Backend | FastAPI |
| Frontend | Streamlit (MVP) |
| OCR | PyMuPDF → Tesseract (cascade) |

---

## Core Modules

### 1. Configuration (src/core/config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    pinecone_api_key: str
    data_dir: str = "data"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. Language Detection (src/core/language.py)

```python
import re
from enum import Enum

class Language(Enum):
    ARABIC = "ar"
    ENGLISH = "en"
    MALAY = "ms"

def detect_language(text: str) -> Language:
    arabic = len(re.findall(r'[\u0600-\u06FF]', text))
    total = len(text.replace(" ", ""))
    if total == 0: return Language.ENGLISH
    return Language.ARABIC if arabic/total > 0.5 else Language.ENGLISH
```

### 3. Base Scraper (src/scrapers/base.py) - DRY

```python
from abc import ABC, abstractmethod
from pathlib import Path
import requests, time

class BaseScraper(ABC):
    """DRY: All scrapers inherit common logic"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source = source_name
        self.base_url = base_url
        self.data_dir = Path(f"data/{source_name.lower()}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download_pdf(self, url: str) -> Path:
        time.sleep(1)  # Polite crawling
        resp = requests.get(url, timeout=30)
        filename = url.split("/")[-1]
        path = self.data_dir / filename
        path.write_bytes(resp.content)
        return path
    
    @abstractmethod
    def get_pdf_urls(self) -> list[str]:
        """Each scraper implements its own URL discovery"""
        pass
    
    def run(self) -> list[dict]:
        results = []
        for url in self.get_pdf_urls():
            path = self.download_pdf(url)
            results.append({"source": self.source, "file": str(path), "url": url})
        return results
```

### 4. BNM Scraper (src/scrapers/bnm.py)

```python
from bs4 import BeautifulSoup
import requests
from .base import BaseScraper

class BNMScraper(BaseScraper):
    def __init__(self):
        super().__init__("BNM", "https://www.bnm.gov.my")
    
    def get_pdf_urls(self) -> list[str]:
        resp = requests.get(f"{self.base_url}/shariah")
        soup = BeautifulSoup(resp.text, "html.parser")
        return [a["href"] for a in soup.find_all("a", href=True) 
                if a["href"].endswith(".pdf")]
```

### 5. PDF Extractor (src/processors/pdf_extractor.py)

```python
import fitz
from src.core.language import detect_language

def extract_pdf(path: str) -> dict:
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    return {
        "text": text,
        "pages": len(doc),
        "language": detect_language(text).value
    }
```

### 6. Arabic Cleaner (src/processors/arabic.py)

```python
import re

def normalize_arabic(text: str) -> str:
    text = re.sub(r'[\u064B-\u0652\u0670]', '', text)  # Diacritics
    text = re.sub(r'[إأٱآا]', 'ا', text)  # Alef variants
    return text
```

### 7. RAG Pipeline (src/ai/rag.py)

```python
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from src.core.config import settings

llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", 
                    api_key=settings.anthropic_api_key)

def query_rag(question: str, vector_store) -> dict:
    chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=vector_store.as_retriever(),
        return_source_documents=True
    )
    result = chain.invoke({"query": question})
    return {"answer": result["result"], 
            "sources": [d.metadata for d in result["source_documents"]]}
```

### 8. ChatService (src/services/chat.py)

```python
from src.core.language import detect_language
from src.ai.rag import query_rag

class ChatService:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def ask(self, question: str) -> dict:
        lang = detect_language(question)
        result = query_rag(question, self.vector_store)
        result["language"] = lang.value
        return result
```

### 9. FastAPI (src/api/main.py)

```python
from fastapi import FastAPI
from pydantic import BaseModel
from src.services.chat import ChatService

app = FastAPI(title="Agent Deen")

class Query(BaseModel):
    question: str

@app.post("/chat")
async def chat(q: Query):
    service = ChatService(vector_store)  # DI in production
    return service.ask(q.question)
```

---

## Requirements

```txt
fastapi==0.109.0
uvicorn==0.27.0
anthropic==0.18.1
langchain==0.1.9
langchain-anthropic==0.1.5
langchain-openai==0.0.5
pinecone-client==3.0.0
pymupdf==1.23.21
beautifulsoup4==4.12.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
streamlit==1.31.0
```

## Environment (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
```

## Run Commands

```bash
# Install
pip install -r requirements.txt

# Run API
uvicorn src.api.main:app --reload

# Run Streamlit
streamlit run app.py

# Run Scraper
python -c "from src.scrapers.bnm import BNMScraper; print(BNMScraper().run())"
```
