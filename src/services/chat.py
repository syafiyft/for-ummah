"""
Chat service - main orchestrator for Agent Deen.
This is the service layer that coordinates all components.
"""

from dataclasses import dataclass
from datetime import datetime
import logging

from src.core.language import Language, detect_language
from src.ai.rag import RAGPipeline, RAGResponse
from src.vector_db import PineconeStore

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """Response from the chat service."""
    answer: str
    sources: list[dict]
    language: str
    confidence: str
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "language": self.language,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class ChatService:
    """
    Main chat service for Agent Deen.
    
    Orchestrates:
    - Language detection
    - RAG querying
    - Response formatting
    """
    
    def __init__(self, vector_store: PineconeStore | None = None):
        """
        Initialize chat service.
        
        Args:
            vector_store: Optional vector store (will create if not provided)
        """
        self.rag = RAGPipeline(vector_store)
        logger.info("ChatService initialized")
    
    def ask(
        self,
        question: str,
        language: str | None = None,
    ) -> ChatResponse:
        """
        Process a user question.
        
        Args:
            question: User's question in any supported language
            language: Preferred response language code ("ar", "en", "ms")
            
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
        
        # Query RAG
        rag_response = self.rag.query(
            question=question,
            language_preference=lang_pref,
        )
        
        return ChatResponse(
            answer=rag_response.answer,
            sources=rag_response.sources,
            language=rag_response.query_language.value,
            confidence=rag_response.confidence,
            timestamp=datetime.now().isoformat(),
        )
    
    def get_health(self) -> dict:
        """Check service health."""
        return {
            "status": "healthy",
            "model": self.rag.llm.model,
        }
