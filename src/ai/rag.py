"""
RAG (Retrieval Augmented Generation) pipeline for Agent Deen.
Uses Ollama for FREE local LLM inference.
"""

from dataclasses import dataclass
import logging

from src.core import settings
from src.core.language import Language, detect_language
from src.core.exceptions import AIError
from src.vector_db import PineconeStore
from .prompts import SHARIAH_PROMPT
from .ollama_llm import OllamaLLM

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""
    answer: str
    sources: list[dict]
    query_language: Language
    confidence: str  # "High", "Medium", "Low"
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "query_language": self.query_language.value,
            "confidence": self.confidence,
        }


class RAGPipeline:
    """
    RAG pipeline combining Pinecone retrieval with Ollama LLM.
    100% FREE local inference.
    """
    
    def __init__(self, vector_store: PineconeStore | None = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            vector_store: Optional PineconeStore instance
        """
        # Initialize Ollama LLM (FREE)
        self.llm = OllamaLLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )
        
        # Vector store (lazy load if not provided)
        self._vector_store = vector_store
        
        logger.info(f"RAG Pipeline initialized with Ollama model: {settings.ollama_model}")
    
    @property
    def vector_store(self) -> PineconeStore:
        """Lazy load vector store."""
        if self._vector_store is None:
            self._vector_store = PineconeStore()
        return self._vector_store
    
    def query(
        self,
        question: str,
        language_preference: Language | None = None,
        top_k: int | None = None,
    ) -> RAGResponse:
        """
        Query the RAG system.
        
        Args:
            question: User's question (in any supported language)
            language_preference: Preferred response language
            top_k: Number of documents to retrieve
            
        Returns:
            RAGResponse with answer and sources
        """
        # Detect query language
        query_lang = detect_language(question)
        response_lang = language_preference or query_lang
        
        if response_lang == Language.MIXED:
            response_lang = Language.ENGLISH
        
        # Retrieve relevant documents
        docs = self.vector_store.search(question, top_k=top_k or settings.rag_top_k)
        
        # Build context from retrieved docs
        context = "\n\n---\n\n".join([
            f"[Source: {d['metadata'].get('source', 'Unknown')}]\n{d['text']}"
            for d in docs
        ])
        
        # Build prompt
        prompt = SHARIAH_PROMPT.format(
            context=context,
            question=question,
            query_language=query_lang.display_name,
            response_language=response_lang.display_name,
        )
        
        # Call Ollama LLM
        try:
            answer = self.llm.generate(
                prompt,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            
        except Exception as e:
            logger.error(f"Ollama LLM error: {e}")
            raise AIError(f"Query failed: {e}")
        
        # Extract sources
        sources = self._extract_sources(docs)
        
        # Calculate confidence
        confidence = self._calculate_confidence(docs)
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            query_language=query_lang,
            confidence=confidence,
        )
    
    def _extract_sources(self, documents: list[dict]) -> list[dict]:
        """Extract source metadata from documents."""
        sources = []
        
        for doc in documents:
            # Get file/title info for display
            file_info = doc["metadata"].get("title", "") or doc["metadata"].get("filename", "")
            
            # Get page number and total pages if available
            page_num = doc["metadata"].get("page_number")
            total_pages = doc["metadata"].get("total_pages")
            
            source = {
                "source": doc["metadata"].get("source", "Unknown"),
                "file": file_info,
                "page": page_num,
                "total_pages": total_pages,
                "snippet": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                "score": doc.get("score", 0),
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, documents: list[dict]) -> str:
        """Calculate confidence level based on retrieved documents."""
        count = len(documents)
        
        if count >= 4:
            return "High"
        elif count >= 2:
            return "Medium"
        else:
            return "Low"


# Convenience function
def query_rag(question: str, **kwargs) -> RAGResponse:
    """
    Quick query function.
    
    Args:
        question: User's question
        **kwargs: Additional arguments for RAGPipeline.query
        
    Returns:
        RAGResponse
    """
    pipeline = RAGPipeline()
    return pipeline.query(question, **kwargs)
