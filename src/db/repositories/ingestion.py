"""
Repository for ingestion history operations.
Handles CRUD for the ingestion_history table.
"""

import logging
from datetime import datetime
from uuid import UUID

from src.db.client import get_supabase_client
from src.db.models import IngestionRecord

logger = logging.getLogger(__name__)

TABLE_NAME = "ingestion_history"


class IngestionRepository:
    """Repository for ingestion history operations."""

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

    def log(
        self,
        type: str,
        source: str,
        filename: str,
        status: str,
        document_id: UUID | str | None = None,
        error_message: str | None = None,
        chunks_created: int = 0,
        duration_seconds: float | None = None
    ) -> IngestionRecord:
        """
        Log an ingestion event.

        Args:
            type: Ingestion type ('url', 'upload', 'auto_update')
            source: Source name
            filename: Filename
            status: Status ('success', 'failed', 'skipped')
            document_id: Related document ID (optional)
            error_message: Error message if failed
            chunks_created: Number of chunks created
            duration_seconds: Processing duration

        Returns:
            Created ingestion record
        """
        data = {
            "type": type,
            "source": source,
            "filename": filename,
            "status": status,
        }

        if document_id:
            data["document_id"] = str(document_id)
        if error_message:
            data["error_message"] = error_message
        if chunks_created:
            data["chunks_created"] = chunks_created
        if duration_seconds is not None:
            data["duration_seconds"] = duration_seconds

        result = self.table.insert(data).execute()

        if result.data:
            return IngestionRecord(**result.data[0])
        raise Exception("Failed to log ingestion")

    def get_all(self, limit: int = 100, type: str | None = None, status: str | None = None) -> list[IngestionRecord]:
        """
        Get all ingestion records.

        Args:
            limit: Maximum records to return
            type: Filter by type
            status: Filter by status

        Returns:
            List of ingestion records
        """
        query = self.table.select("*")

        if type:
            query = query.eq("type", type)
        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).limit(limit)
        result = query.execute()

        return [IngestionRecord(**row) for row in result.data]

    def get_by_document(self, document_id: UUID | str) -> list[IngestionRecord]:
        """
        Get ingestion records for a specific document.

        Args:
            document_id: Document UUID

        Returns:
            List of ingestion records
        """
        result = (
            self.table
            .select("*")
            .eq("document_id", str(document_id))
            .order("created_at", desc=True)
            .execute()
        )

        return [IngestionRecord(**row) for row in result.data]

    def get_recent(self, hours: int = 24) -> list[IngestionRecord]:
        """
        Get recent ingestion records.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent ingestion records
        """
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        result = (
            self.table
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )

        return [IngestionRecord(**row) for row in result.data]

    def count(self, status: str | None = None) -> int:
        """
        Count ingestion records.

        Args:
            status: Filter by status

        Returns:
            Number of records
        """
        query = self.table.select("id", count="exact")

        if status:
            query = query.eq("status", status)

        result = query.execute()
        return result.count or 0

    def get_stats(self) -> dict:
        """
        Get ingestion statistics.

        Returns:
            Dict with success/failed/skipped counts
        """
        return {
            "success": self.count(status="success"),
            "failed": self.count(status="failed"),
            "skipped": self.count(status="skipped"),
            "total": self.count(),
        }

    def to_legacy_format(self, records: list[IngestionRecord]) -> list[dict]:
        """
        Convert records to legacy JSON format for backward compatibility.

        Args:
            records: List of ingestion records

        Returns:
            List of dicts in legacy format
        """
        return [
            {
                "id": str(r.id),
                "timestamp": r.created_at.isoformat() if r.created_at else None,
                "type": r.type,
                "source": r.source,
                "filename": r.filename,
                "status": r.status,
                "error": r.error_message,
                "chunks_created": r.chunks_created,
                "duration_seconds": r.duration_seconds,
            }
            for r in records
        ]


# Convenience function
def get_ingestion_repository() -> IngestionRepository:
    """Get an IngestionRepository instance."""
    return IngestionRepository()
