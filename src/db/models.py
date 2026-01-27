"""
Pydantic models for database entities.
Used for type safety and serialization.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from uuid import UUID


class Document(BaseModel):
    """Document record in the database."""
    id: UUID | None = None
    filename: str
    original_filename: str
    source: str  # 'bnm', 'sc_malaysia', 'manual', etc.
    source_url: str | None = None
    title: str | None = None
    storage_path: str  # Path in Supabase Storage
    file_size_bytes: int | None = None
    total_pages: int | None = None
    extraction_method: str | None = None  # 'digital' or 'ocr'
    status: str = "pending"  # 'pending', 'processing', 'indexed', 'failed'
    error_message: str | None = None
    created_at: datetime | None = None
    indexed_at: datetime | None = None

    class Config:
        from_attributes = True


class ChatSession(BaseModel):
    """Chat session record."""
    id: UUID | None = None
    title: str = "New Chat"
    model: str = "ollama"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Chat message record."""
    id: UUID | None = None
    session_id: UUID
    role: str  # 'user' or 'assistant'
    content: str
    sources: list[dict[str, Any]] | None = None  # Citation metadata for assistant
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class IngestionRecord(BaseModel):
    """Ingestion history record."""
    id: UUID | None = None
    document_id: UUID | None = None
    type: str  # 'url', 'upload', 'auto_update'
    source: str
    filename: str
    status: str  # 'success', 'failed', 'skipped'
    error_message: str | None = None
    chunks_created: int = 0
    duration_seconds: float | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class JobStatus(BaseModel):
    """Job status record (singleton)."""
    id: int = 1
    status: str = "idle"  # 'idle', 'running', 'completed', 'failed'
    message: str | None = None
    progress: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
