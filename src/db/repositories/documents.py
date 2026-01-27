"""
Repository for document operations.
Handles CRUD for the documents table.
"""

import logging
from datetime import datetime
from uuid import UUID

from src.db.client import get_supabase_client
from src.db.models import Document

logger = logging.getLogger(__name__)

TABLE_NAME = "documents"


class DocumentRepository:
    """Repository for document database operations."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-load Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    @property
    def table(self):
        """Get table interface."""
        return self.client.table(TABLE_NAME)

    def create(self, doc: Document) -> Document:
        """
        Create a new document record.

        Args:
            doc: Document model with data to insert

        Returns:
            Created document with ID populated
        """
        data = doc.model_dump(exclude={"id", "created_at", "indexed_at"}, exclude_none=True)

        result = self.table.insert(data).execute()

        if result.data:
            return Document(**result.data[0])
        raise Exception("Failed to create document")

    def get_by_id(self, doc_id: UUID | str) -> Document | None:
        """
        Get a document by ID.

        Args:
            doc_id: Document UUID

        Returns:
            Document if found, None otherwise
        """
        result = self.table.select("*").eq("id", str(doc_id)).execute()

        if result.data:
            return Document(**result.data[0])
        return None

    def get_by_source_and_filename(self, source: str, filename: str) -> Document | None:
        """
        Get a document by source and filename (unique constraint).

        Args:
            source: Source name
            filename: Filename

        Returns:
            Document if found, None otherwise
        """
        result = (
            self.table
            .select("*")
            .eq("source", source)
            .eq("filename", filename)
            .execute()
        )

        if result.data:
            return Document(**result.data[0])
        return None

    def get_all(self, source: str | None = None, status: str | None = None) -> list[Document]:
        """
        Get all documents, optionally filtered.

        Args:
            source: Filter by source
            status: Filter by status

        Returns:
            List of documents
        """
        query = self.table.select("*")

        if source:
            query = query.eq("source", source)
        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True)
        result = query.execute()

        return [Document(**row) for row in result.data]

    def update(self, doc_id: UUID | str, updates: dict) -> Document | None:
        """
        Update a document.

        Args:
            doc_id: Document UUID
            updates: Dictionary of fields to update

        Returns:
            Updated document, or None if not found
        """
        result = (
            self.table
            .update(updates)
            .eq("id", str(doc_id))
            .execute()
        )

        if result.data:
            return Document(**result.data[0])
        return None

    def update_status(
        self,
        doc_id: UUID | str,
        status: str,
        error_message: str | None = None,
        indexed_at: datetime | None = None
    ) -> Document | None:
        """
        Update document status.

        Args:
            doc_id: Document UUID
            status: New status ('pending', 'processing', 'indexed', 'failed')
            error_message: Error message if status is 'failed'
            indexed_at: Timestamp when indexing completed

        Returns:
            Updated document
        """
        updates = {"status": status}
        if error_message:
            updates["error_message"] = error_message
        if indexed_at:
            updates["indexed_at"] = indexed_at.isoformat()

        return self.update(doc_id, updates)

    def delete(self, doc_id: UUID | str) -> bool:
        """
        Delete a document.

        Args:
            doc_id: Document UUID

        Returns:
            True if deleted, False otherwise
        """
        result = self.table.delete().eq("id", str(doc_id)).execute()
        return len(result.data) > 0

    def exists(self, source: str, filename: str) -> bool:
        """
        Check if a document exists.

        Args:
            source: Source name
            filename: Filename

        Returns:
            True if document exists
        """
        return self.get_by_source_and_filename(source, filename) is not None

    def count(self, source: str | None = None, status: str | None = None) -> int:
        """
        Count documents.

        Args:
            source: Filter by source
            status: Filter by status

        Returns:
            Number of documents
        """
        query = self.table.select("id", count="exact")

        if source:
            query = query.eq("source", source)
        if status:
            query = query.eq("status", status)

        result = query.execute()
        return result.count or 0


# Convenience function
def get_document_repository() -> DocumentRepository:
    """Get a DocumentRepository instance."""
    return DocumentRepository()
