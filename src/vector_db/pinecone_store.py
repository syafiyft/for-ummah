"""
Pinecone vector store for document retrieval.
Uses Ollama for FREE local embeddings.
"""

import logging
from typing import Iterator

import requests
from pinecone import Pinecone, ServerlessSpec

from src.core import settings
from src.core.exceptions import VectorDBError
from src.processors.chunker import TextChunk

logger = logging.getLogger(__name__)


class OllamaEmbeddings:
    """Local embeddings using Ollama (FREE)."""
    
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self.dimension = 768  # nomic-embed-text dimension
    
    def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=30,
        )
        
        if response.status_code != 200:
            raise VectorDBError(f"Ollama error: {response.text}")
        
        # Ensure all values are floats (Pinecone requirement)
        return [float(v) for v in response.json()["embedding"]]


class PineconeStore:
    """
    Wrapper around Pinecone for document storage and retrieval.
    Uses Ollama for FREE local embeddings.
    """
    
    def __init__(self):
        """Initialize Pinecone connection and Ollama embeddings."""
        if not settings.pinecone_api_key:
            raise VectorDBError("PINECONE_API_KEY not set")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        
        # Initialize Ollama embeddings (FREE)
        self.embeddings = OllamaEmbeddings()
        
        # Ensure index exists
        self._ensure_index()
        
        # Get index reference
        self.index = self.pc.Index(settings.pinecone_index)
        
        logger.info(f"Pinecone store initialized: {settings.pinecone_index}")
    
    def _ensure_index(self):
        """Create index if it doesn't exist."""
        existing = [idx.name for idx in self.pc.list_indexes()]
        if settings.pinecone_index not in existing:
            logger.info(f"Creating Pinecone index: {settings.pinecone_index}")
            self.pc.create_index(
                name=settings.pinecone_index,
                dimension=768,  # nomic-embed-text dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.pinecone_region,
                ),
            )
    
    def add_chunks(self, chunks: Iterator[TextChunk] | list[TextChunk]) -> int:
        """
        Add text chunks to the vector store.
        
        Args:
            chunks: Iterator or list of TextChunk objects
            
        Returns:
            Number of chunks added
        """
        vectors = []
        count = 0
        
        for chunk in chunks:
            embedding = self.embeddings.embed(chunk.text)
            
            # Build metadata with page number and language
            metadata = {
                "text": chunk.text[:1000],  # Pinecone metadata limit
                **{k: str(v)[:500] for k, v in chunk.metadata.items()},
            }
            
            # Add page number if available
            if hasattr(chunk, 'page_number') and chunk.page_number is not None:
                metadata["page_number"] = chunk.page_number
            
            # Add total pages if available
            if hasattr(chunk, 'total_pages') and chunk.total_pages is not None:
                metadata["total_pages"] = chunk.total_pages
            
            # Add language for trilingual indexing
            if hasattr(chunk, 'language') and chunk.language:
                metadata["language"] = chunk.language
            
            # Add original_text for source display (preserves original language)
            if hasattr(chunk, 'original_text') and chunk.original_text:
                metadata["original_text"] = chunk.original_text[:1000]
            
            vectors.append({
                "id": f"chunk_{count}_{hash(chunk.text) % 1000000}",
                "values": embedding,
                "metadata": metadata,
            })
            count += 1
            
            # Batch upsert every 50 vectors
            if len(vectors) >= 50:
                self.index.upsert(vectors=vectors)
                logger.info(f"Indexed {count} chunks...")
                vectors = []
        
        # Upsert remaining
        if vectors:
            self.index.upsert(vectors=vectors)
        
        logger.info(f"Total indexed: {count} chunks")
        return count
    
    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results (default from settings)
            
        Returns:
            List of matching documents with metadata
        """
        top_k = top_k or settings.rag_top_k
        
        # Get query embedding
        query_embedding = self.embeddings.embed(query)
        
        # Search
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        
        # Format results
        documents = []
        for match in results.matches:
            documents.append({
                "text": match.metadata.get("text", ""),
                "score": match.score,
                "metadata": match.metadata,
            })
        
        return documents
