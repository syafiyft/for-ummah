"""
Ingestion service to handle document processing pipeline.
1. Download/Save File
2. Extract Text (PDF)
3. Chunk Text
4. Index in Vector DB
"""

import time
import logging
from pathlib import Path

from src.scrapers.manual import ManualScraper
from src.processors.pdf_extractor import extract_pdf
from src.processors.chunker import chunk_with_pages
from src.vector_db.pinecone_store import PineconeStore
from src.core import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service to handle document ingestion pipeline.
    """
    
    def __init__(self):
        self.scraper = ManualScraper()
        self.vector_store = PineconeStore()
    
    def ingest_from_url(self, url: str) -> dict:
        """
        Ingest a document from a direct URL.
        """
        logger.info(f"Ingesting URL: {url}")
        
        # 1. Download
        doc = self.scraper.scrape_from_url(url)
        if not doc:
            raise ValueError(f"Failed to download from URL: {url}")
        
        # 2. Process
        return self._process_document(doc.file_path, source_url=url)

    def ingest_file(self, file_content: bytes, filename: str) -> dict:
        """
        Ingest a specific file content (e.g. from upload).
        """
        logger.info(f"Ingesting file: {filename}")
        
        # 1. Save file
        save_path = self.scraper.data_dir / filename
        save_path.write_bytes(file_content)
        
        # 2. Process
        return self._process_document(save_path, source_url=f"upload://{filename}")

    def _process_document(self, file_path: Path, source_url: str) -> dict:
        """
        Run extraction, chunking, and indexing pipeline.
        """
        start_time = time.time()
        
        # 1. Extract Text
        logger.info(f"Extracting text from: {file_path.name}")
        extraction = extract_pdf(file_path)
        
        if not extraction.text.strip():
            logger.warning("Empty text extracted")
            return {
                "status": "error",
                "message": "No text could be extracted from the document",
                "file": file_path.name
            }

        # 2. Chunk
        logger.info(f"Chunking text (Pages: {extraction.pages})")
        chunks = chunk_with_pages(
            page_texts=extraction.page_texts if extraction.page_texts else [],
            total_pages=extraction.pages,
            metadata={
                "source": "Manual",
                "file": file_path.name,
                "url": source_url,
                "title": file_path.stem.replace("_", " ").title(),
            }
        )
        
        # Fallback if no page_texts (e.g. weird PDF format) but we have full text
        if not chunks and extraction.text:
             from src.processors.chunker import chunk_text
             chunks = chunk_text(
                 extraction.text,
                 metadata={
                    "source": "Manual",
                    "file": file_path.name,
                    "url": source_url,
                    "title": file_path.stem.replace("_", " ").title(),
                }
             )

        # 3. Index
        logger.info(f"Indexing {len(chunks)} chunks")
        count = self.vector_store.add_chunks(chunks)
        
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "file": file_path.name,
            "pages": extraction.pages,
            "chunks": count,
            "extraction_method": extraction.method.value,
            "duration_seconds": round(duration, 2)
        }
