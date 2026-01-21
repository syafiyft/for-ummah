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

from src.services import ChatService

logger = logging.getLogger(__name__)

# Service instance (lazy loaded)
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get or create chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Agent Deen API...")
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


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    answer: str
    sources: list[dict]
    language: str
    confidence: str
    model_used: str = "ollama"
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str


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


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Ask Agent Deen a question.
    
    Supports questions in Arabic, English, and Malay.
    Responds in the same language as the question (or specified language).
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        service = get_chat_service()
        response = service.ask(
            question=request.question,
            language=request.language,
            model=request.model,
        )
        
        return ChatResponse(
            **response.to_dict(),
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
