"""
Database module for Supabase integration.
Provides client, storage service, and repository classes.
"""

from src.db.client import get_supabase_client
from src.db.storage import StorageService
from src.db.models import (
    Document,
    ChatSession,
    ChatMessage,
    IngestionRecord,
    JobStatus,
)

__all__ = [
    "get_supabase_client",
    "StorageService",
    "Document",
    "ChatSession",
    "ChatMessage",
    "IngestionRecord",
    "JobStatus",
]
