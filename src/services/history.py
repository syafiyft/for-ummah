"""
History service to manage chat history and ingestion logs.
Uses Supabase when configured, falls back to local JSON files.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import uuid

from src.core import settings
from src.db.client import is_supabase_configured

logger = logging.getLogger(__name__)


class HistoryService:
    """
    Manages chat history and ingestion logs.
    Uses Supabase repositories when configured, falls back to JSON files.
    """

    def __init__(self):
        self.data_dir = settings.data_dir
        self._use_supabase = is_supabase_configured()

        # Lazy-loaded repositories
        self._chat_repo = None
        self._ingestion_repo = None
        self._job_status_repo = None

        # JSON fallback paths
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        self.chat_history_file = self.data_dir / "chat_history.json"
        self.ingestion_history_file = self.data_dir / "ingestion_history.json"
        self.job_status_file = self.data_dir / "job_status.json"

        # Initialize JSON files only if not using Supabase
        if not self._use_supabase:
            logger.info("Supabase not configured, using JSON file storage")
            self._init_files()
        else:
            logger.info("Using Supabase for history storage")

    @property
    def chat_repo(self):
        """Lazy-load chat repository."""
        if self._chat_repo is None and self._use_supabase:
            from src.db.repositories.chat import ChatRepository
            self._chat_repo = ChatRepository()
        return self._chat_repo

    @property
    def ingestion_repo(self):
        """Lazy-load ingestion repository."""
        if self._ingestion_repo is None and self._use_supabase:
            from src.db.repositories.ingestion import IngestionRepository
            self._ingestion_repo = IngestionRepository()
        return self._ingestion_repo

    @property
    def job_status_repo(self):
        """Lazy-load job status repository."""
        if self._job_status_repo is None and self._use_supabase:
            from src.db.repositories.job_status import JobStatusRepository
            self._job_status_repo = JobStatusRepository()
        return self._job_status_repo

    # --- JSON File Methods (Fallback) ---

    def _init_files(self):
        """Initialize JSON files if they don't exist."""
        if not self.chat_history_file.exists():
            self._save_json(self.chat_history_file, [])

        if not self.ingestion_history_file.exists():
            self._save_json(self.ingestion_history_file, [])

        if not self.job_status_file.exists():
            self._save_json(self.job_status_file, {"status": "idle", "message": "System ready", "progress": 0.0})

    def _load_json(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: List[Dict]):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")

    # --- Chat History Methods ---

    def create_chat(self, title: str = "New Chat", model: str = "ollama") -> str:
        """Create a new chat session."""
        if self._use_supabase:
            session = self.chat_repo.create_session(title, model)
            return str(session.id)

        # JSON fallback
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "model": model,
            "messages": []
        }

        history = self._load_json(self.chat_history_file)
        history.append(session)
        self._save_json(self.chat_history_file, history)

        return session_id

    def get_chat(self, session_id: str) -> Optional[Dict]:
        """Get a specific chat session."""
        if self._use_supabase:
            return self.chat_repo.get_session_with_messages(session_id)

        # JSON fallback
        history = self._load_json(self.chat_history_file)
        for chat in history:
            if chat["id"] == session_id:
                return chat
        return None

    def get_all_chats(self) -> List[Dict]:
        """Get all chat sessions (summary only)."""
        if self._use_supabase:
            sessions = self.chat_repo.get_all_sessions()
            return [
                {
                    "id": str(s.id),
                    "title": s.title,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in sessions
            ]

        # JSON fallback
        history = self._load_json(self.chat_history_file)
        history.sort(key=lambda x: x["updated_at"], reverse=True)
        return [{"id": c["id"], "title": c["title"], "updated_at": c["updated_at"]} for c in history]

    def update_chat(self, session_id: str, message: Dict, title_update: str = None):
        """Add a message to a chat session."""
        if self._use_supabase:
            # Add the message
            self.chat_repo.add_message(
                session_id=session_id,
                role=message.get("role"),
                content=message.get("content"),
                sources=message.get("sources")
            )
            # Update title if needed
            if title_update:
                self.chat_repo.update_session(session_id, title=title_update)
            return

        # JSON fallback
        history = self._load_json(self.chat_history_file)
        for chat in history:
            if chat["id"] == session_id:
                chat["messages"].append(message)
                chat["updated_at"] = datetime.now().isoformat()
                if title_update:
                    chat["title"] = title_update
                break
        self._save_json(self.chat_history_file, history)

    def rename_chat(self, session_id: str, new_title: str) -> bool:
        """Rename a chat session."""
        if self._use_supabase:
            return self.chat_repo.rename_session(session_id, new_title)

        # JSON fallback
        history = self._load_json(self.chat_history_file)
        for chat in history:
            if chat["id"] == session_id:
                chat["title"] = new_title
                chat["updated_at"] = datetime.now().isoformat()
                self._save_json(self.chat_history_file, history)
                return True
        return False

    def delete_chat(self, session_id: str):
        """Delete a chat session."""
        if self._use_supabase:
            self.chat_repo.delete_session(session_id)
            return

        # JSON fallback
        history = self._load_json(self.chat_history_file)
        history = [c for c in history if c["id"] != session_id]
        self._save_json(self.chat_history_file, history)

    # --- Ingestion History Methods ---

    def log_ingestion(
        self,
        type: str,
        source: str,
        filename: str,
        status: str,
        error: str = None,
        chunks_created: int = 0,
        duration_seconds: float = None
    ):
        """Log an ingestion event."""
        if self._use_supabase:
            self.ingestion_repo.log(
                type=type,
                source=source,
                filename=filename,
                status=status,
                error_message=error,
                chunks_created=chunks_created,
                duration_seconds=duration_seconds
            )
            return

        # JSON fallback
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "source": source,
            "filename": filename,
            "status": status,
            "error": error
        }

        history = self._load_json(self.ingestion_history_file)
        history.append(log_entry)
        self._save_json(self.ingestion_history_file, history)

    def get_ingestion_history(self) -> List[Dict]:
        """Get full ingestion history."""
        if self._use_supabase:
            records = self.ingestion_repo.get_all()
            return self.ingestion_repo.to_legacy_format(records)

        # JSON fallback
        history = self._load_json(self.ingestion_history_file)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history

    # --- Job Status Methods (For Progress Bar) ---

    def update_job_status(self, status: str, message: str = None, progress: float = 0.0, details: Dict = None):
        """Update current job status (volatile, for UI polling)."""
        if self._use_supabase:
            self.job_status_repo.update(status, message, progress, details)
            return

        # JSON fallback
        data = {
            "status": status,
            "message": message,
            "progress": progress,
            "updated_at": datetime.now().isoformat(),
            "details": details or {}
        }
        self._save_json(self.job_status_file, data)

    def get_job_status(self) -> Dict:
        """Get current job status."""
        if self._use_supabase:
            return self.job_status_repo.to_dict()

        # JSON fallback
        return self._load_json(self.job_status_file) or {"status": "idle", "progress": 0.0}
