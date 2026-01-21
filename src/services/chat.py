"""
Chat service - main orchestrator for Agent Deen.
This is the service layer that coordinates all components.
"""

from dataclasses import dataclass
from datetime import datetime
import logging

from src.core.language import Language, detect_language
from src.ai.rag import RAGPipeline, RAGResponse, LLM_OLLAMA, LLM_CLAUDE
from src.vector_db import PineconeStore

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from the chat service."""
    answer: str
    sources: list[dict]
    language: str
    confidence: str
    model_used: str
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "language": self.language,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "timestamp": self.timestamp,
        }


class ChatService:
    """
    Main chat service for Agent Deen.
    
    Orchestrates:
    - Language detection
    - RAG querying (with Ollama or Claude)
    - Response formatting
    """
    
    def __init__(self, vector_store: PineconeStore | None = None):
        """
        Initialize chat service.
        
        Args:
            vector_store: Optional vector store (will create if not provided)
        """
        self.vector_store = vector_store
        # RAG pipelines are created per-request based on model choice
        self._rag_ollama = None
        self._rag_claude = None
        logger.info("ChatService initialized")
    
    def _get_rag(self, model: str) -> RAGPipeline:
        """Get or create RAG pipeline for the specified model."""
        if model == LLM_CLAUDE:
            if self._rag_claude is None:
                self._rag_claude = RAGPipeline(
                    vector_store=self.vector_store,
                    llm_type=LLM_CLAUDE,
                )
            return self._rag_claude
        else:
            if self._rag_ollama is None:
                self._rag_ollama = RAGPipeline(
                    vector_store=self.vector_store,
                    llm_type=LLM_OLLAMA,
                )
            return self._rag_ollama
    
    def ask(
        self,
        question: str,
        language: str | None = None,
        model: str = "ollama",
    ) -> ChatResponse:
        """
        Process a user question.
        
        Args:
            question: User's question in any supported language
            language: Preferred response language code ("ar", "en", "ms")
            model: LLM to use ("ollama" or "claude")
            
        Returns:
            ChatResponse with answer and metadata
        """
        # Parse language preference
        lang_pref = None
        if language:
            try:
                lang_pref = Language(language)
            except ValueError:
                pass
        
        # Get RAG pipeline for selected model
        rag = self._get_rag(model)
        
        # Query RAG
        rag_response = rag.query(
            question=question,
            language_preference=lang_pref,
        )
        
        return ChatResponse(
            answer=rag_response.answer,
            sources=rag_response.sources,
            language=rag_response.query_language.value,
            confidence=rag_response.confidence,
            model_used=rag_response.model_used,
            timestamp=datetime.now().isoformat(),
        )
    
    def get_health(self) -> dict:
        """Check service health."""
        return {
            "status": "healthy",
            "models_available": ["ollama", "claude"],
        }

