"""
RAG (Retrieval Augmented Generation) pipeline for Agent Deen.
Supports both Ollama (FREE) and Claude Haiku (paid, better quality).
"""

from dataclasses import dataclass
import logging
import re

from src.core import settings
from src.core.language import Language, detect_language
from src.core.exceptions import AIError
from src.vector_db import PineconeStore
from src.vector_db import PineconeStore
from .prompts import SHARIAH_PROMPT, CONTEXTUAL_REWRITE_PROMPT
from .ollama_llm import OllamaLLM
from .translator import ensure_response_language

# Optional Claude import (only if API key is set)
try:
    from .claude_llm import ClaudeLLM
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

logger = logging.getLogger(__name__)

# LLM model types
LLM_OLLAMA = "ollama"
LLM_CLAUDE = "claude"


def translate_query_to_english(query: str, source_lang: Language) -> str:
    """
    Translate a non-English query to English for better vector search.
    Uses free Google Translate via deep-translator.
    """
    if source_lang == Language.ENGLISH:
        return query
    
    try:
        from deep_translator import GoogleTranslator
        
        lang_code = {
            Language.MALAY: "ms",
            Language.ARABIC: "ar",
            Language.MIXED: "auto",
        }.get(source_lang, "auto")
        
        translator = GoogleTranslator(source=lang_code, target="en")
        translated = translator.translate(query)
        logger.info(f"Translated query: '{query}' → '{translated}'")
        return translated
    except Exception as e:
        logger.warning(f"Query translation failed: {e}, using original")
        return query


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""
    answer: str
    sources: list[dict]
    query_language: Language
    confidence: str  # "High", "Medium", "Low"
    model_used: str = "ollama"  # Track which model was used
    reranked: bool = False  # Track if reranking was applied
    
    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "query_language": self.query_language.value,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "reranked": self.reranked,
        }


class RAGPipeline:
    """
    RAG pipeline combining Pinecone retrieval, Reranking, and LLM.
    Supports Ollama (FREE) and Claude Haiku (paid, better).
    """
    
    def __init__(
        self, 
        vector_store: PineconeStore | None = None,
        llm_type: str = LLM_OLLAMA,
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            vector_store: Optional PineconeStore instance
            llm_type: "ollama" (free) or "claude" (paid, better)
        """
        self.llm_type = llm_type
        
        # Initialize Reranker (Lazy load or on init)
        # Using cross-encoder/ms-marco-MiniLM-L-6-v2 (fast & accurate)
        try:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder(settings.rerank_model, default_activation_function=None)
            logger.info(f"Reranker initialized: {settings.rerank_model}")
        except Exception as e:
            logger.warning(f"Reranker init failed: {e}. Reranking will be skipped.")
            self.reranker = None
        
        # Initialize LLM based on type
        if llm_type == LLM_CLAUDE and CLAUDE_AVAILABLE:
            try:
                self.llm = ClaudeLLM(
                    model=settings.llm_model,
                    api_key=settings.anthropic_api_key
                )
                logger.info(f"RAG Pipeline initialized with Claude: {settings.llm_model}")
            except Exception as e:
                logger.warning(f"Claude init failed: {e}, falling back to Ollama")
                self.llm = OllamaLLM(
                    model=settings.ollama_model,
                    base_url=settings.ollama_base_url,
                )
                self.llm_type = LLM_OLLAMA
        else:
            self.llm = OllamaLLM(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
            logger.info(f"RAG Pipeline initialized with Ollama: {settings.ollama_model}")
        
        # Vector store (lazy load if not provided)
        self._vector_store = vector_store
    
    @property
    def vector_store(self) -> PineconeStore:
        """Lazy load vector store."""
        if self._vector_store is None:
            self._vector_store = PineconeStore()
        return self._vector_store
    
    def rewrite_query(self, question: str, history: list[dict]) -> str:
        """
        Rewrite user question based on chat history to make it standalone.
        """
        if not history:
            return question
            
        try:
            # Format history for prompt
            history_text = ""
            # Use last 6 messages
            recent = history[-6:]
            for msg in recent:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"
            
            prompt = CONTEXTUAL_REWRITE_PROMPT.format(
                history=history_text,
                question=question
            )
            
            # Fast generation with lower temp
            rewritten = self.llm.generate(prompt, temperature=0.1, max_tokens=100)
            rewritten = rewritten.strip()
            
            # Simple validation: if too short or empty, use original
            if not rewritten or len(rewritten) < 3:
                return question
                
            logger.info(f"Query Rewrite: '{question}' -> '{rewritten}'")
            return rewritten
            
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}")
            return question

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
        
        # Translate query to English for better vector search
        search_query = translate_query_to_english(question, query_lang)
        
        # 1. Retrieve Candidate Documents (High Recall)
        # Use a larger top_k (e.g., 50) to cast a wide net
        retrieval_k = top_k or settings.rag_top_k
        docs = self.vector_store.search(search_query, top_k=retrieval_k)
        
        # 2. Rerank Documents (High Precision)
        reranked = False
        relevant_docs = docs
        
        if self.reranker and docs:
            try:
                # Prepare pairs for cross-encoder: (query, doc_text)
                pairs = [[search_query, d['text']] for d in docs]
                
                # Predict scores (higher is better)
                scores = self.reranker.predict(pairs)
                
                # Attach new scores to docs
                for doc, score in zip(docs, scores):
                    doc['score'] = float(score)  # Update score with reranker score
                    doc['metadata']['rerank_score'] = float(score)
                
                # Sort by new score (descending)
                docs.sort(key=lambda x: x['score'], reverse=True)
                
                # Select top N for context (e.g., 10)
                final_k = settings.rag_rerank_top_k
                relevant_docs = docs[:final_k]
                
                # Filter by simple threshold if score is too low (e.g., < -5 logits or < 0.2 probability)
                # CrossEncoder scores are logits (unbounded), so hard to threshold universally.
                # We trust the relative ordering more.
                reranked = True
                logger.info(f"Reranked {len(docs)} docs -> Top {len(relevant_docs)} for context")
                
            except Exception as e:
                logger.error(f"Reranking failed: {e}. Using original vector order.")
        
        # 3. Filter low-relevance chunks (if not using reranker, or as safety net)
        # If we didn't rerank, we use cosine score threshold.
        # If we did rerank, we rely on top-k, but we could add a logit threshold if needed.
        if not reranked:
            threshold = settings.rag_relevance_threshold
            relevant_docs = [d for d in relevant_docs if d.get("score", 0) >= threshold]
            if len(relevant_docs) < len(docs):
                logger.info(f"Filtered low-relevance chunks (below {threshold})")
        
        # If no relevant docs, return early with "not enough info" message
        if not relevant_docs:
            logger.warning("No chunks passed selection/threshold")
            
            no_info_msg = "I apologize, but I could not find sufficient information in the provided Shariah sources to answer your question."
            
            # Translate message if needed
            final_msg = ensure_response_language(no_info_msg, response_lang)
            
            return RAGResponse(
                answer=final_msg,
                sources=[],
                query_language=query_lang,
                confidence="Low",
                model_used=self.llm_type,
                reranked=reranked,
            )
        
        # Build context from retrieved docs with source citation
        context_parts = []
        for i, d in enumerate(relevant_docs):
            source = d['metadata'].get('source', 'Unknown')
            title = d['metadata'].get('title', '')
            page = d['metadata'].get('page_number', '')

            # Clean up filename/title for context (same as _extract_sources)
            raw_filename = d['metadata'].get('filename', '')
            clean_regex = r'^[a-f0-9]{12}[_\s]+'
            clean_title = re.sub(clean_regex, '', title)
            clean_filename = re.sub(clean_regex, '', raw_filename)
            
            # Use title if available, otherwise cleaned filename
            display_title = clean_title if title and title != "Unknown" else clean_filename

            source_label = f"[Source {i+1}: {source}"
            if display_title:
                source_label += f" - {display_title}"
            if page:
                source_label += f", Page {page}"
            source_label += "]"
            
            context_parts.append(f"{source_label}\n{d['text']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build prompt
        prompt = SHARIAH_PROMPT.format(
            knowledge_sources="\n".join([f"- {s}" for s in settings.knowledge_sources]),
            context=context,
            question=question,  # Use original question for context
            query_language=query_lang.display_name,
            response_language=response_lang.display_name,
        )
        
        # Call LLM (Ollama or Claude)
        try:
            answer = self.llm.generate(
                prompt,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            
            # Ensure response is in the correct language (fallback translation)
            answer = ensure_response_language(answer, response_lang)
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise AIError(f"Query failed: {e}")
        
        # Extract sources (only from relevant docs)
        sources = self._extract_sources(relevant_docs)
        
        # Calculate confidence (based on relevant docs)
        confidence = self._calculate_confidence(relevant_docs)
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            query_language=query_lang,
            confidence=confidence,
            model_used=self.llm_type,
            reranked=reranked,
        )
    
    def _extract_sources(self, documents: list[dict]) -> list[dict]:
        """Extract source metadata from documents."""
        sources = []
        import re
        
        for doc in documents:
            # Get file/title info for display
            raw_filename = doc["metadata"].get("filename", "")
            title = doc["metadata"].get("title", "")
            
            # Clean up filename/title (remove 12-char hex ID if present)
            # Matches "a1b2c3d4e5f6 " or "a1b2c3d4e5f6_" at start
            clean_regex = r'^[a-f0-9]{12}[_\s]+'
            
            clean_filename = re.sub(clean_regex, '', raw_filename)
            clean_title = re.sub(clean_regex, '', title)
            
            # Use title if available, otherwise cleaned filename
            file_info = clean_title if title and title != "Unknown" else clean_filename
            
            # Get page number and total pages if available
            page_num = doc["metadata"].get("page_number")
            total_pages = doc["metadata"].get("total_pages")
            
            # Use original_text for snippet (preserves source language)
            # Fall back to translated text if original not available
            snippet_text = doc["metadata"].get("original_text") or doc["text"]
            snippet = snippet_text[:200] + "..." if len(snippet_text) > 200 else snippet_text
            
            # Get score (could be reranker score or cosine)
            score = doc.get("score", 0)
            
            source = {
                "source": doc["metadata"].get("source", "Unknown"),
                "file": file_info,  # Display name (cleaned)
                "filename": raw_filename,  # Original filename for PDF URL
                "page": page_num,
                "total_pages": total_pages,
                "snippet": snippet,
                "score": score,  # Now reflects reranker score if active
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
