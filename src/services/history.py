
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import uuid

from src.core import settings

logger = logging.getLogger(__name__)

class HistoryService:
    """
    Manages chat history and ingestion logs using local JSON files.
    """
    
    def __init__(self):
        self.data_dir = settings.data_dir
        # Ensure data directory exists
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
        self.chat_history_file = self.data_dir / "chat_history.json"
        self.ingestion_history_file = self.data_dir / "ingestion_history.json"
        self._init_files()

    def _init_files(self):
        """Initialize JSON files if they don't exist."""
        if not self.chat_history_file.exists():
            self._save_json(self.chat_history_file, [])
            
        if not self.ingestion_history_file.exists():
            self._save_json(self.ingestion_history_file, [])

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
        history = self._load_json(self.chat_history_file)
        for chat in history:
            if chat["id"] == session_id:
                return chat
        return None

    def get_all_chats(self) -> List[Dict]:
        """Get all chat sessions (summary only)."""
        history = self._load_json(self.chat_history_file)
        # Sort by updated_at desc
        history.sort(key=lambda x: x["updated_at"], reverse=True)
        return [{"id": c["id"], "title": c["title"], "updated_at": c["updated_at"]} for c in history]

    def update_chat(self, session_id: str, message: Dict, title_update: str = None):
        """Add a message to a chat session."""
        history = self._load_json(self.chat_history_file)
        for chat in history:
            if chat["id"] == session_id:
                chat["messages"].append(message)
                chat["updated_at"] = datetime.now().isoformat()
                if title_update:
                    chat["title"] = title_update
                break
        self._save_json(self.chat_history_file, history)

    def delete_chat(self, session_id: str):
        """Delete a chat session."""
        history = self._load_json(self.chat_history_file)
        history = [c for c in history if c["id"] != session_id]
        self._save_json(self.chat_history_file, history)

    # --- Ingestion History Methods ---

    def log_ingestion(self, type: str, source: str, filename: str, status: str, error: str = None):
        """Log an ingestion event."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": type, # "url" or "upload"
            "source": source,
            "filename": filename,
            "status": status, # "success" or "failed"
            "error": error
        }
        
        history = self._load_json(self.ingestion_history_file)
        history.append(log_entry)
        self._save_json(self.ingestion_history_file, history)

    def get_ingestion_history(self) -> List[Dict]:
        """Get full ingestion history."""
        history = self._load_json(self.ingestion_history_file)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history
