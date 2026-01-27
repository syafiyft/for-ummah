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
from src.api import pdf_preview
from src.db.client import is_supabase_configured

logger = logging.getLogger(__name__)

# Lazy-loaded Supabase services
_storage_service = None
_document_repo = None


def get_storage_service():
    """Get storage service if Supabase is configured."""
    global _storage_service
    if _storage_service is None and is_supabase_configured():
        from src.db.storage import StorageService
        _storage_service = StorageService()
    return _storage_service


def get_document_repo():
    """Get document repository if Supabase is configured."""
    global _document_repo
    if _document_repo is None and is_supabase_configured():
        from src.db.repositories.documents import DocumentRepository
        _document_repo = DocumentRepository()
    return _document_repo

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
    
    # Start Scheduler
    from src.services.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    
    yield
    
    stop_scheduler()
    logger.info("Shutting down Agent Deen API...")


# FastAPI app
app = FastAPI(
    title="Agent Deen API",
    description="Trilingual AI Shariah Compliance Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(pdf_preview.router)

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


class RenameChatRequest(BaseModel):
    """Request for renaming a chat."""
    title: str


@app.patch("/history/chat/{session_id}/rename", tags=["History"])
async def rename_chat_session(session_id: str, request: RenameChatRequest):
    """Rename a chat session."""
    success = get_history_service().rename_chat(session_id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"status": "renamed", "id": session_id, "title": request.title}


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
        
        # Prepare context from history
        chat_context = None
        if request.session_id:
            session = history.get_chat(request.session_id)
            if session:
                chat_context = session.get("messages", [])

        # 1. Get Answer
        response = service.ask(
            question=request.question,
            language=request.language,
            model=request.model,
            chat_history=chat_context,
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

        # Log success with extended details
        get_history_service().log_ingestion(
            type="url",
            source=request.url,
            filename=result.get("file", ""),
            status="success",
            chunks_created=result.get("chunks", 0),
            duration_seconds=result.get("duration_seconds")
        )

        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        get_history_service().log_ingestion(
            type="url",
            source=request.url,
            filename="",
            status="failed",
            error=str(e)
        )
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

        # Log success with extended details
        get_history_service().log_ingestion(
            type="upload",
            source=file.filename,
            filename=result.get("file", ""),
            status="success",
            chunks_created=result.get("chunks", 0),
            duration_seconds=result.get("duration_seconds")
        )

        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        get_history_service().log_ingestion(
            type="upload",
            source=file.filename,
            filename="",
            status="failed",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pdf/{source}/{filename:path}", tags=["PDF"])
async def get_pdf(source: str, filename: str, redirect: bool = True):
    """
    Serve a PDF file from Supabase Storage or local data directory.

    Args:
        source: Source folder (e.g., "manual", "bnm")
        filename: PDF filename (can include spaces, will be URL-decoded)
        redirect: If True and Supabase is configured, redirect to signed URL

    Returns:
        PDF file or redirect to signed URL
    """
    from fastapi.responses import FileResponse, RedirectResponse
    from pathlib import Path
    from urllib.parse import unquote
    from src.core import settings
    import io

    # URL decode the filename (handles %20 for spaces, etc.)
    filename = unquote(filename)

    # Security: Block path traversal attempts
    if ".." in filename or ".." in source or "/" in source:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Ensure .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename = filename + '.pdf'

    storage = get_storage_service()

    # Try Supabase Storage first
    if storage:
        try:
            storage_path = f"{source.lower()}/{filename}"

            # Option 1: Redirect to signed URL (faster, less bandwidth)
            if redirect:
                signed_url = storage.get_signed_url(storage_path, expires_in=3600)
                if signed_url:
                    return RedirectResponse(url=signed_url)

            # Option 2: Stream the file through the API
            content = storage.download_pdf(storage_path, use_cache=True)
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
            )
        except Exception as e:
            logger.debug(f"Storage fetch failed, falling back to local: {e}")

    # Fall back to local file
    source_dir = settings.data_dir / source.lower()
    file_path = source_dir / filename

    # Security: Ensure file is within data directory
    try:
        file_path = file_path.resolve()
        data_dir = settings.data_dir.resolve()
        if not str(file_path).startswith(str(data_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    # Check if file exists - if not, try case-insensitive search
    if not file_path.exists():
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
async def list_pdfs(source: str | None = None):
    """
    List all available PDFs.
    Queries from database if Supabase is configured, otherwise scans local directory.

    Args:
        source: Optional filter by source (e.g., 'bnm', 'manual')
    """
    from pathlib import Path
    from src.core import settings

    doc_repo = get_document_repo()

    # Use database if Supabase is configured
    if doc_repo:
        try:
            documents = doc_repo.get_all(source=source)
            pdfs = [
                {
                    "id": str(doc.id),
                    "source": doc.source,
                    "filename": doc.filename,
                    "title": doc.title,
                    "size_bytes": doc.file_size_bytes,
                    "total_pages": doc.total_pages,
                    "status": doc.status,
                    "storage_path": doc.storage_path,
                    "url": f"/pdf/{doc.source}/{doc.filename}",
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
                }
                for doc in documents
            ]
            return {"pdfs": pdfs, "count": len(pdfs), "storage": "supabase"}
        except Exception as e:
            logger.warning(f"Database query failed, falling back to local: {e}")

    # Fall back to local directory scan
    pdfs = []
    data_dir = settings.data_dir

    if data_dir.exists():
        for source_dir in data_dir.iterdir():
            if source_dir.is_dir() and source_dir.name not in ["processed", ".cache"]:
                # Apply source filter if provided
                if source and source_dir.name.lower() != source.lower():
                    continue

                for pdf_file in source_dir.glob("*.pdf"):
                    pdfs.append({
                        "source": source_dir.name,
                        "filename": pdf_file.name,
                        "size_bytes": pdf_file.stat().st_size,
                        "url": f"/pdf/{source_dir.name}/{pdf_file.name}"
                    })

    return {"pdfs": pdfs, "count": len(pdfs), "storage": "local"}



@app.get("/pdf/signed-url/{source}/{filename:path}", tags=["PDF"])
async def get_pdf_signed_url(source: str, filename: str, expires_in: int = 3600):
    """
    Get a signed URL for direct PDF access from Supabase Storage.

    Args:
        source: Source folder (e.g., "manual", "bnm")
        filename: PDF filename
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        Signed URL for the PDF
    """
    from urllib.parse import unquote

    filename = unquote(filename)

    # Security check
    if ".." in filename or ".." in source or "/" in source:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not filename.lower().endswith('.pdf'):
        filename = filename + '.pdf'

    storage = get_storage_service()
    if not storage:
        raise HTTPException(
            status_code=501,
            detail="Supabase Storage not configured. Use /pdf/{source}/{filename} instead."
        )

    try:
        storage_path = f"{source.lower()}/{filename}"
        signed_url = storage.get_signed_url(storage_path, expires_in=expires_in)

        if not signed_url:
            raise HTTPException(status_code=404, detail="PDF not found in storage")

        return {
            "signed_url": signed_url,
            "expires_in": expires_in,
            "storage_path": storage_path
        }
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TriggerRequest(BaseModel):
    sources: list[str] = ["BNM", "SC"]

@app.post("/admin/trigger-update", tags=["Admin"])
async def trigger_update(request: TriggerRequest | None = None):
    """
    Manually trigger the background update job.
    """
    from src.services.scheduler import run_daily_update, scheduler
    
    sources = request.sources if request else ["BNM", "SC"]
    
    # Run in background via scheduler to avoid blocking
    job = scheduler.add_job(run_daily_update, 'date', run_date=datetime.now(), args=[sources])
    
    return {"status": "started", "job_id": job.id, "message": f"Update job triggered for {sources}"}


@app.get("/admin/job-status", tags=["Admin"])
async def get_job_status():
    """Get the status of the background update job."""
    return get_history_service().get_job_status()


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

