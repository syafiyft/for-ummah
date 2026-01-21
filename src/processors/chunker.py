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
    page_number: int | None = None  # Source page number (if available)
    total_pages: int | None = None  # Total pages in source document
    language: str = "en"  # ISO 639-1 code (en, ms, ar)
    original_text: str | None = None  # Original untranslated text for display
    
    def to_dict(self) -> dict:
        result = {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "language": self.language,
            **self.metadata,
        }
        if self.page_number is not None:
            result["page_number"] = self.page_number
        if self.total_pages is not None:
            result["total_pages"] = self.total_pages
        if self.original_text is not None:
            result["original_text"] = self.original_text
        return result


def _clean_chunk_start(text: str) -> str:
    """
    Clean up the start of a chunk to begin at a sentence boundary.
    Removes partial sentences from the beginning.
    """
    if not text:
        return text
    
    # If starts with lowercase or mid-sentence characters, find first sentence start
    first_char = text.lstrip()[0] if text.strip() else ''
    
    # If already starts with uppercase, number, or bullet, it's likely clean
    if first_char.isupper() or first_char.isdigit() or first_char in '•–-(':
        return text
    
    # Find the first sentence boundary (. ! ? followed by space/newline and uppercase)
    import re
    match = re.search(r'[.!?؟。]\s+([A-Z\u0600-\u06FF\d])', text)
    if match:
        return text[match.start() + 1:].lstrip()
    
    # If no sentence boundary found, return as-is
    return text


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    metadata: dict | None = None,
) -> list[TextChunk]:
    """
    Split text into overlapping chunks with clean sentence boundaries.
    
    Ensures:
    - Chunks end at sentence boundaries (. ! ? etc.)
    - Chunks start at sentence beginnings
    - No broken words at start/end
    
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
            text=text.strip(),
            chunk_index=0,
            start_char=0,
            end_char=len(text),
            metadata=metadata,
        )]
    
    chunks = []
    start = 0
    chunk_index = 0
    
    # Sentence-ending punctuation
    sentence_ends = '.!?؟。'
    
    while start < len(text):
        # Determine end position
        end = min(start + chunk_size, len(text))
        
        if end < len(text):
            # Try to break at sentence boundary (search backwards)
            best_break = end
            search_start = max(start + chunk_size // 2, start + 100)  # Don't search too far back
            
            for i in range(end, search_start, -1):
                if text[i-1] in sentence_ends:
                    # Check if followed by space/newline (not mid-abbreviation)
                    if i >= len(text) or text[i] in ' \n\t\r':
                        best_break = i
                        break
            
            # If no sentence break found, try paragraph break
            if best_break == end:
                for i in range(end, search_start, -1):
                    if text[i-1] == '\n':
                        best_break = i
                        break
            
            # Last resort: break at last space (don't break mid-word)
            if best_break == end:
                for i in range(end, search_start, -1):
                    if text[i] in ' \n\t':
                        best_break = i + 1
                        break
            
            end = best_break
        
        # Extract and clean the chunk
        chunk_text_raw = text[start:end]
        
        # Clean start of chunk (remove partial sentences from overlap)
        if start > 0:  # Only clean if not the first chunk
            chunk_text_content = _clean_chunk_start(chunk_text_raw).strip()
        else:
            chunk_text_content = chunk_text_raw.strip()
        
        if chunk_text_content and len(chunk_text_content) > 20:  # Don't add tiny chunks
            chunks.append(TextChunk(
                text=chunk_text_content,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
                metadata=metadata,
            ))
            chunk_index += 1
        
        # Move start with overlap, but find a clean sentence start
        next_start = end - chunk_overlap
        
        # Find next sentence start after next_start
        for i in range(next_start, min(next_start + 200, len(text))):
            if i > 0 and text[i-1] in sentence_ends and (i >= len(text) or text[i] in ' \n\t'):
                next_start = i
                break
        
        # Prevent infinite loop
        if next_start <= start:
            next_start = end
        
        start = next_start
    
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


def chunk_with_pages(
    page_texts: list[tuple[int, str]],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    metadata: dict | None = None,
    total_pages: int | None = None,
) -> list[TextChunk]:
    """
    Chunk text while preserving page number information.
    
    Each chunk will include the page number(s) it came from.
    For chunks that span multiple pages, uses the starting page.
    
    Args:
        page_texts: List of (page_number, text) tuples
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks
        metadata: Base metadata to attach
        total_pages: Total number of pages in the source document
        
    Returns:
        List of TextChunk objects with page_number and total_pages set
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    metadata = metadata or {}
    
    # Auto-detect total pages if not provided
    if total_pages is None and page_texts:
        total_pages = len(page_texts)
    
    chunks = []
    chunk_index = 0
    
    # Process each page separately to maintain page tracking
    for page_num, page_text in page_texts:
        if not page_text or not page_text.strip():
            continue
        
        # Chunk this page's text
        page_chunks = chunk_text(
            page_text, 
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            metadata=metadata,
        )
        
        # Add page number and total pages to each chunk from this page
        for chunk in page_chunks:
            chunk.page_number = page_num
            chunk.total_pages = total_pages
            chunk.chunk_index = chunk_index
            chunks.append(chunk)
            chunk_index += 1
    
    return chunks
