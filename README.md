# Agent Deen

Trilingual AI Shariah Chatbot for Islamic Finance (Arabic, English, Malay)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run the API
uvicorn src.api.main:app --reload

# Run Streamlit UI
streamlit run app.py
```

## Project Structure

```
src/
├── core/       # Config, language detection
├── scrapers/   # Web scrapers (BNM, AAOIFI, JAKIM)
├── processors/ # PDF extraction, Arabic cleaning
├── ai/         # RAG pipeline with Claude
├── services/   # ChatService orchestrator
└── api/        # FastAPI endpoints
```

## Features

- 🌍 Trilingual: Arabic (العربية), English, Bahasa Melayu
- 📚 Sources: BNM, AAOIFI, SC Malaysia, JAKIM
- 🤖 AI: Claude 3.5 Sonnet + RAG
- 📄 Smart PDF extraction with Arabic OCR
