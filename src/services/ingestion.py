"""
Ingestion service to handle document processing pipeline.
1. Download/Save File (+ upload to Supabase Storage if configured)
2. Extract Text (PDF)
3. Chunk Text
4. Index in Vector DB
5. Create document record in database
"""

import time
import logging
from pathlib import Path
from datetime import datetime

from src.scrapers.manual import ManualScraper
from src.processors.pdf_extractor import extract_pdf
from src.processors.chunker import chunk_with_pages
from src.vector_db.pinecone_store import PineconeStore
from src.core import settings
from src.db.client import is_supabase_configured

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service to handle document ingestion pipeline.
    Uploads PDFs to Supabase Storage when configured.
    """

    def __init__(self):
        self.scraper = ManualScraper()
        self.vector_store = PineconeStore()
        self._use_supabase = is_supabase_configured()

        # Lazy-loaded services
        self._storage_service = None
        self._document_repo = None
        self._history_service = None

    @property
    def storage_service(self):
        """Lazy-load storage service."""
        if self._storage_service is None and self._use_supabase:
            from src.db.storage import StorageService
            self._storage_service = StorageService()
        return self._storage_service

    @property
    def document_repo(self):
        """Lazy-load document repository."""
        if self._document_repo is None and self._use_supabase:
            from src.db.repositories.documents import DocumentRepository
            self._document_repo = DocumentRepository()
        return self._document_repo

    @property
    def history_service(self):
        """Lazy-load history service."""
        if self._history_service is None:
            from src.services.history import HistoryService
            self._history_service = HistoryService()
        return self._history_service

    def ingest_from_url(self, url: str) -> dict:
        """
        Ingest a document from a direct URL.
        """
        logger.info(f"Ingesting URL: {url}")

        # 1. Download
        doc = self.scraper.scrape_from_url(url)
        if not doc:
            raise ValueError(f"Failed to download from URL: {url}")

        # 2. Process (with storage upload)
        return self._process_document(doc.file_path, source_url=url)

    def ingest_file(self, file_content: bytes, filename: str) -> dict:
        """
        Ingest a specific file content (e.g. from upload).
        """
        logger.info(f"Ingesting file: {filename}")

        # Determine source directory
        source_name = "manual"
        save_dir = self.scraper.data_dir

        # 1. Save file locally
        save_path = save_dir / filename
        save_path.write_bytes(file_content)

        # 2. Upload to Supabase Storage if configured
        storage_path = None
        if self._use_supabase:
            try:
                storage_path = self.storage_service.upload_pdf(
                    file_content=file_content,
                    source=source_name,
                    filename=filename
                )
                logger.info(f"Uploaded to storage: {storage_path}")
            except Exception as e:
                logger.warning(f"Failed to upload to storage: {e}")

        # 3. Process
        return self._process_document(
            save_path,
            source_url=f"upload://{filename}",
            storage_path=storage_path
        )

    def is_already_indexed(self, source: str, filename: str) -> bool:
        """
        Check if a document is already indexed in Supabase.

        Args:
            source: Source name (e.g., 'bnm', 'manual')
            filename: PDF filename

        Returns:
            True if document exists and is indexed
        """
        if not self._use_supabase:
            return False

        existing = self.document_repo.get_by_source_and_filename(source, filename)
        if existing and existing.status == "indexed":
            return True
        return False

    def _process_document(
        self,
        file_path: Path,
        source_url: str,
        source_name: str = None,
        storage_path: str = None,
        force_reindex: bool = False
    ) -> dict:
        """
        Run extraction, chunking, and indexing pipeline.
        Creates document record in database if Supabase is configured.

        Args:
            file_path: Path to PDF file
            source_url: Original URL or upload path
            source_name: Source category (e.g., 'bnm', 'manual')
            storage_path: Supabase Storage path if already uploaded
            force_reindex: If True, reindex even if already in database
        """
        start_time = time.time()
        doc_id = None

        # Determine source if not provided
        if not source_name:
            parent_name = file_path.parent.name.lower()
            if parent_name in ["bnm", "sc_malaysia", "aaoifi", "manual"]:
                source_name = parent_name
            else:
                source_name = "manual"

        # Check if already indexed in Supabase (skip if so)
        if self._use_supabase and not force_reindex:
            existing = self.document_repo.get_by_source_and_filename(source_name, file_path.name)
            if existing:
                if existing.status == "indexed":
                    logger.info(f"Skipping already indexed document: {file_path.name}")
                    
                    self.history_service.log_ingestion(
                        type="ingest",
                        source=source_name,
                        filename=file_path.name,
                        status="skipped",
                        error="Already indexed"
                    )

                    return {
                        "status": "skipped",
                        "message": "Document already indexed in database",
                        "file": file_path.name,
                        "document_id": str(existing.id),
                        "existing_status": existing.status
                    }
                elif existing.status == "processing":
                    logger.info(f"Document is currently being processed: {file_path.name}")
                    return {
                        "status": "skipped",
                        "message": "Document is currently being processed",
                        "file": file_path.name,
                        "document_id": str(existing.id),
                        "existing_status": existing.status
                    }
                # If status is 'failed' or 'pending', we'll reprocess it

        # Create document record (pending status)
        if self._use_supabase:
            try:
                from src.db.models import Document

                # Upload to storage if not already uploaded
                if not storage_path:
                    storage_path = self.storage_service.upload_pdf_from_path(
                        file_path=file_path,
                        source=source_name
                    )

                # Check if document already exists (to avoid duplicate key error on re-index)
                existing_doc = self.document_repo.get_by_source_and_filename(source_name, file_path.name)
                
                if existing_doc:
                    # Update existing record
                    logger.info(f"Updating existing document record: {existing_doc.id}")
                    self.document_repo.update(existing_doc.id, {
                        "status": "processing",
                        "storage_path": storage_path,
                        "file_size_bytes": file_path.stat().st_size,
                        "title": file_path.stem.replace("_", " ").title(),
                        "extraction_method": None # Reset for new extraction
                    })
                    doc_id = existing_doc.id
                else:
                    # Create new document record
                    doc = Document(
                        filename=file_path.name,
                        original_filename=file_path.name,
                        source=source_name,
                        source_url=source_url,
                        title=file_path.stem.replace("_", " ").title(),
                        storage_path=storage_path,
                        file_size_bytes=file_path.stat().st_size,
                        status="processing"
                    )
                    created_doc = self.document_repo.create(doc)
                    doc_id = created_doc.id
                    logger.info(f"Created document record: {doc_id}")

            except Exception as e:
                logger.warning(f"Failed to create/update document record: {e}")

        # 1. Extract Text
        logger.info(f"Extracting text from: {file_path.name}")
        extraction = extract_pdf(file_path)

        if not extraction.text.strip():
            logger.warning("Empty text extracted")

            # Update document status to failed
            if doc_id and self._use_supabase:
                self.document_repo.update_status(
                    doc_id, "failed",
                    error_message="No text could be extracted from the document"
                )

            # Log failure
            self.history_service.log_ingestion(
                type="ingest",
                source=source_name,
                filename=file_path.name,
                status="failed",
                error="No text extracted"
            )

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
                "source": source_name,
                "file": file_path.name,
                "url": source_url,
                "title": file_path.stem.replace("_", " ").title(),
            }
        )

        # Fallback if no page_texts but we have full text
        if not chunks and extraction.text:
            from src.processors.chunker import chunk_text
            chunks = chunk_text(
                extraction.text,
                metadata={
                    "source": source_name,
                    "file": file_path.name,
                    "url": source_url,
                    "title": file_path.stem.replace("_", " ").title(),
                }
            )

        # 3. Index
        logger.info(f"Indexing {len(chunks)} chunks")
        count = self.vector_store.add_chunks(chunks)

        duration = time.time() - start_time

        # Update document record to indexed
        if doc_id and self._use_supabase:
            self.document_repo.update(doc_id, {
                "status": "indexed",
                "total_pages": extraction.pages,
                "extraction_method": extraction.method.value,
                "indexed_at": datetime.now().isoformat()
            })

        # Log success to history
        self.history_service.log_ingestion(
            type="ingest",
            source=source_name,
            filename=file_path.name,
            status=f"Indexed ({count} chunks)",
            chunks_created=count,
            duration_seconds=round(duration, 2)
        )

        return {
            "status": "success",
            "file": file_path.name,
            "pages": extraction.pages,
            "chunks": count,
            "extraction_method": extraction.method.value,
            "duration_seconds": round(duration, 2),
            "document_id": str(doc_id) if doc_id else None
        }
