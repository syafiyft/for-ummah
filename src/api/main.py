"""
FastAPI backend for Agent Deen.
Thin layer - delegates all logic to services.
"""

from contextlib import asynccontextmanager
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services import ChatService
from src.services.ingestion import IngestionService
from src.services.history import HistoryService

logger = logging.getLogger(__name__)

# Service instances (lazy loaded)
_chat_service: ChatService | None = None
_ingestion_service: IngestionService | None = None
_history_service: HistoryService | None = None


def get_chat_service() -> ChatService:
    """Get or create chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def get_ingestion_service() -> IngestionService:
    """Get or create ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service


def get_history_service() -> HistoryService:
    """Get or create history service instance."""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Agent Deen API...")
    get_history_service() # Initialize history files
    yield
    logger.info("Shutting down Agent Deen API...")


# FastAPI app
app = FastAPI(
    title="Agent Deen API",
    description="Trilingual AI Shariah Compliance Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    question: str
    language: str | None = None  # Optional: "ar", "en", "ms"
    model: str = "ollama"  # "ollama" (free) or "claude" (paid)
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    answer: str
    sources: list[dict]
    language: str
    confidence: str
    model_used: str = "ollama"
    timestamp: str
    session_id: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str


class IngestUrlRequest(BaseModel):
    """Request for URL ingestion."""
    url: str


class IngestResponse(BaseModel):
    """Response for ingestion."""
    status: str
    file: str
    pages: int = 0
    chunks: int = 0
    duration_seconds: float = 0.0
    message: str | None = None


# Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Deen",
        "description": "Trilingual AI Shariah Compliance Assistant",
        "version": "1.0.0",
        "languages": ["ar", "en", "ms"],
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
    )


# --- HISTORY ENDPOINTS ---

@app.get("/history/chats", response_model=list[dict], tags=["History"])
async def list_chats():
    """List all chat sessions."""
    return get_history_service().get_all_chats()


@app.get("/history/chat/{session_id}", tags=["History"])
async def get_chat_details(session_id: str):
    """Get full details of a specific chat."""
    chat = get_history_service().get_chat(session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat


@app.post("/history/chat", tags=["History"])
async def create_chat_session(title: str = "New Chat", model: str = "ollama"):
    """Create a new chat session."""
    session_id = get_history_service().create_chat(title, model)
    return {"id": session_id, "title": title}


@app.delete("/history/chat/{session_id}", tags=["History"])
async def delete_chat_session(session_id: str):
    """Delete a chat session."""
    get_history_service().delete_chat(session_id)
    return {"status": "deleted", "id": session_id}


@app.get("/history/sources", tags=["History", "Ingestion"])
async def list_ingestion_history():
    """List detailed ingestion history."""
    return get_history_service().get_ingestion_history()


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Ask Agent Deen a question.
    
    Supports questions in Arabic, English, and Malay.
    Responds in the same language as the question (or specified language).
    Logs conversation to history if session_id is provided.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        service = get_chat_service()
        history = get_history_service()
        
        # 1. Get Answer
        response = service.ask(
            question=request.question,
            language=request.language,
            model=request.model,
        )
        
        # 2. Log to History (if session_id provided)
        session_id = request.session_id
        if session_id:
            # Check if valid session
            if history.get_chat(session_id):
                # Update with User Question
                history.update_chat(session_id, {
                    "role": "user",
                    "content": request.question,
                    "timestamp": datetime.now().isoformat()
                })
                # Update with AI Answer
                history.update_chat(session_id, {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources, # Store sources for history
                    "timestamp": datetime.now().isoformat()
                }, title_update=request.question[:50] if len(history.get_chat(session_id)['messages']) <= 2 else None)
        
        return ChatResponse(
            **response.to_dict(),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/url", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_url(request: IngestUrlRequest):
    """
    Ingest a document from a direct URL.
    Downloads, extracts text, chunks, and indexes it.
    """
    try:
        service = get_ingestion_service()
        result = service.ingest_from_url(request.url)
        
        # Log success
        get_history_service().log_ingestion("url", request.url, result.get("file", ""), "success")
        
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        get_history_service().log_ingestion("url", request.url, "", "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/upload", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_upload(file: UploadFile = File(...)):
    """
    Ingest an uploaded PDF file.
    Extracts text, chunks, and indexes it.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        content = await file.read()
        service = get_ingestion_service()
        result = service.ingest_file(content, file.filename)
        
        # Log success
        get_history_service().log_ingestion("upload", file.filename, result.get("file", ""), "success")
        
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        get_history_service().log_ingestion("upload", file.filename, "", "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pdf/{source}/{filename:path}", tags=["PDF"])
async def get_pdf(source: str, filename: str):
    """
    Serve a PDF file from the data directory.
    
    Args:
        source: Source folder (e.g., "manual", "bnm")
        filename: PDF filename (can include spaces, will be URL-decoded)
    
    Returns:
        PDF file with appropriate headers
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    from urllib.parse import unquote
    from src.core import settings
    
    # URL decode the filename (handles %20 for spaces, etc.)
    filename = unquote(filename)
    
    # Security: Block path traversal attempts
    if ".." in filename or ".." in source or "/" in source:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Ensure .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename = filename + '.pdf'
    
    # Construct file path
    source_dir = settings.data_dir / source.lower()
    file_path = source_dir / filename
    
    # Security: Ensure file is within data directory (prevent path traversal)
    try:
        file_path = file_path.resolve()
        data_dir = settings.data_dir.resolve()
        if not str(file_path).startswith(str(data_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Check if file exists - if not, try case-insensitive search
    if not file_path.exists():
        # Try to find a matching file (case-insensitive, fuzzy match)
        if source_dir.exists():
            filename_lower = filename.lower().replace(' ', '_').replace('-', '_')
            for pdf_file in source_dir.glob("*.pdf"):
                pdf_name_normalized = pdf_file.name.lower().replace(' ', '_').replace('-', '_')
                if filename_lower in pdf_name_normalized or pdf_name_normalized in filename_lower:
                    file_path = pdf_file
                    break
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found: {filename}")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name,
        headers={"Content-Disposition": f"inline; filename=\"{file_path.name}\""}
    )


@app.get("/pdf/list", tags=["PDF"])
async def list_pdfs():
    """
    List all available PDFs in the data directory.
    """
    from pathlib import Path
    from src.core import settings
    
    pdfs = []
    data_dir = settings.data_dir
    
    if data_dir.exists():
        for source_dir in data_dir.iterdir():
            if source_dir.is_dir() and source_dir.name != "processed":
                for pdf_file in source_dir.glob("*.pdf"):
                    pdfs.append({
                        "source": source_dir.name,
                        "filename": pdf_file.name,
                        "size_bytes": pdf_file.stat().st_size,
                        "url": f"/pdf/{source_dir.name}/{pdf_file.name}"
                    })
    
    return {"pdfs": pdfs, "count": len(pdfs)}


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

