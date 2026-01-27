"""
Repository for job status operations.
Handles CRUD for the job_status table (singleton pattern).
"""

import logging
from datetime import datetime
from typing import Any

from src.db.client import get_supabase_client
from src.db.models import JobStatus

logger = logging.getLogger(__name__)

TABLE_NAME = "job_status"
SINGLETON_ID = 1


class JobStatusRepository:
    """Repository for job status operations (singleton table)."""

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

    def get(self) -> JobStatus:
        """
        Get the current job status.

        Returns:
            Current job status (creates default if not exists)
        """
        result = self.table.select("*").eq("id", SINGLETON_ID).execute()

        if result.data:
            return JobStatus(**result.data[0])

        # Return default status if table is empty
        return JobStatus(
            id=SINGLETON_ID,
            status="idle",
            message="System ready",
            progress=0.0,
            details={}
        )

    def update(
        self,
        status: str,
        message: str | None = None,
        progress: float = 0.0,
        details: dict[str, Any] | None = None
    ) -> JobStatus:
        """
        Update the job status.

        Args:
            status: New status ('idle', 'running', 'completed', 'failed')
            message: Status message
            progress: Progress percentage (0.0 to 1.0)
            details: Additional details dict

        Returns:
            Updated job status
        """
        data = {
            "status": status,
            "message": message,
            "progress": progress,
            "updated_at": datetime.now().isoformat(),
        }

        if details is not None:
            data["details"] = details

        result = (
            self.table
            .upsert({"id": SINGLETON_ID, **data})
            .execute()
        )

        if result.data:
            return JobStatus(**result.data[0])

        # Return what we tried to set if update fails
        return JobStatus(id=SINGLETON_ID, **data)

    def set_running(self, message: str, progress: float = 0.0, details: dict | None = None) -> JobStatus:
        """
        Set status to running.

        Args:
            message: Progress message
            progress: Progress percentage
            details: Additional details

        Returns:
            Updated job status
        """
        return self.update("running", message, progress, details)

    def set_completed(self, message: str = "Completed successfully", details: dict | None = None) -> JobStatus:
        """
        Set status to completed.

        Args:
            message: Completion message
            details: Final details

        Returns:
            Updated job status
        """
        return self.update("completed", message, 1.0, details)

    def set_failed(self, message: str, details: dict | None = None) -> JobStatus:
        """
        Set status to failed.

        Args:
            message: Error message
            details: Error details

        Returns:
            Updated job status
        """
        return self.update("failed", message, 0.0, details)

    def set_idle(self, message: str = "System ready") -> JobStatus:
        """
        Set status to idle.

        Args:
            message: Idle message

        Returns:
            Updated job status
        """
        return self.update("idle", message, 0.0, {})

    def to_dict(self) -> dict:
        """
        Get job status as a dict (legacy format).

        Returns:
            Dict with status info
        """
        status = self.get()
        return {
            "status": status.status,
            "message": status.message,
            "progress": status.progress,
            "details": status.details,
            "updated_at": status.updated_at.isoformat() if status.updated_at else None,
        }


# Convenience function
def get_job_status_repository() -> JobStatusRepository:
    """Get a JobStatusRepository instance."""
    return JobStatusRepository()
