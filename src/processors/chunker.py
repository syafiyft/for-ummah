"""
Text chunking for RAG pipeline.

Splits documents into smaller chunks for better retrieval.
Preserves context by using overlapping windows.
"""

from dataclasses import dataclass
from typing import Iterator

from src.core import settings


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            **self.metadata,
        }


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    metadata: dict | None = None,
) -> list[TextChunk]:
    """
    Split text into overlapping chunks.
    
    Uses sentence and paragraph boundaries when possible
    to avoid breaking mid-sentence.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk (default from settings)
        chunk_overlap: Overlap between chunks (default from settings)
        metadata: Metadata to attach to each chunk
        
    Returns:
        List of TextChunk objects
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    metadata = metadata or {}
    
    if not text or len(text) <= chunk_size:
        return [TextChunk(
            text=text,
            chunk_index=0,
            start_char=0,
            end_char=len(text),
            metadata=metadata,
        )]
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Determine end position
        end = start + chunk_size
        
        if end >= len(text):
            end = len(text)
        else:
            # Try to break at sentence boundary
            # Look for . ! ? followed by space or newline
            best_break = end
            
            # Search backwards for good break point
            search_start = max(start + chunk_size // 2, start)
            for i in range(end, search_start, -1):
                if i < len(text) and text[i-1] in '.!?؟。' and (i >= len(text) or text[i] in ' \n\t'):
                    best_break = i
                    break
            
            # If no sentence break, try paragraph break
            if best_break == end:
                for i in range(end, search_start, -1):
                    if i < len(text) and text[i-1] == '\n':
                        best_break = i
                        break
            
            end = best_break
        
        chunk_text_content = text[start:end].strip()
        
        if chunk_text_content:  # Don't add empty chunks
            chunks.append(TextChunk(
                text=chunk_text_content,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
                metadata=metadata,
            ))
            chunk_index += 1
        
        # Move start with overlap
        start = end - chunk_overlap
        if start <= chunks[-1].start_char if chunks else 0:
            start = end  # Prevent infinite loop
    
    return chunks


def chunk_documents(documents: list[dict]) -> Iterator[TextChunk]:
    """
    Chunk multiple documents.
    
    Args:
        documents: List of dicts with 'text' and optional metadata
        
    Yields:
        TextChunk objects for each document
    """
    for doc in documents:
        text = doc.get("text", "")
        
        # Build metadata from document fields
        metadata = {
            k: v for k, v in doc.items() 
            if k != "text" and not k.startswith("_")
        }
        
        for chunk in chunk_text(text, metadata=metadata):
            yield chunk
