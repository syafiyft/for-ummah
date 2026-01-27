"""
Repository classes for database operations.
Each repository handles CRUD operations for a specific table.
"""

from src.db.repositories.documents import DocumentRepository
from src.db.repositories.chat import ChatRepository
from src.db.repositories.ingestion import IngestionRepository
from src.db.repositories.job_status import JobStatusRepository

__all__ = [
    "DocumentRepository",
    "ChatRepository",
    "IngestionRepository",
    "JobStatusRepository",
]
