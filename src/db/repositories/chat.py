"""
Repository for chat operations.
Handles CRUD for chat_sessions and chat_messages tables.
"""

import logging
from datetime import datetime
from uuid import UUID

from src.db.client import get_supabase_client
from src.db.models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

SESSIONS_TABLE = "chat_sessions"
MESSAGES_TABLE = "chat_messages"


class ChatRepository:
    """Repository for chat session and message operations."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-load Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    # --- Session Operations ---

    def create_session(self, title: str = "New Chat", model: str = "ollama") -> ChatSession:
        """
        Create a new chat session.

        Args:
            title: Session title
            model: Model identifier

        Returns:
            Created session with ID populated
        """
        data = {"title": title, "model": model}

        result = self.client.table(SESSIONS_TABLE).insert(data).execute()

        if result.data:
            return ChatSession(**result.data[0])
        raise Exception("Failed to create chat session")

    def get_session(self, session_id: UUID | str) -> ChatSession | None:
        """
        Get a chat session by ID.

        Args:
            session_id: Session UUID

        Returns:
            ChatSession if found, None otherwise
        """
        result = (
            self.client.table(SESSIONS_TABLE)
            .select("*")
            .eq("id", str(session_id))
            .execute()
        )

        if result.data:
            return ChatSession(**result.data[0])
        return None

    def get_all_sessions(self, limit: int = 50) -> list[ChatSession]:
        """
        Get all chat sessions, ordered by most recent.

        Args:
            limit: Maximum sessions to return

        Returns:
            List of sessions (summary only)
        """
        result = (
            self.client.table(SESSIONS_TABLE)
            .select("id, title, model, updated_at")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )

        return [ChatSession(**row) for row in result.data]

    def update_session(
        self,
        session_id: UUID | str,
        title: str | None = None,
        model: str | None = None
    ) -> ChatSession | None:
        """
        Update a chat session.

        Args:
            session_id: Session UUID
            title: New title (optional)
            model: New model (optional)

        Returns:
            Updated session
        """
        updates = {"updated_at": datetime.now().isoformat()}
        if title is not None:
            updates["title"] = title
        if model is not None:
            updates["model"] = model

        result = (
            self.client.table(SESSIONS_TABLE)
            .update(updates)
            .eq("id", str(session_id))
            .execute()
        )

        if result.data:
            return ChatSession(**result.data[0])
        return None

    def delete_session(self, session_id: UUID | str) -> bool:
        """
        Delete a chat session (cascade deletes messages).

        Args:
            session_id: Session UUID

        Returns:
            True if deleted
        """
        result = (
            self.client.table(SESSIONS_TABLE)
            .delete()
            .eq("id", str(session_id))
            .execute()
        )
        return len(result.data) > 0

    def rename_session(self, session_id: UUID | str, new_title: str) -> bool:
        """
        Rename a chat session.

        Args:
            session_id: Session UUID
            new_title: New title

        Returns:
            True if renamed successfully
        """
        result = self.update_session(session_id, title=new_title)
        return result is not None

    # --- Message Operations ---

    def add_message(
        self,
        session_id: UUID | str,
        role: str,
        content: str,
        sources: list[dict] | None = None
    ) -> ChatMessage:
        """
        Add a message to a chat session.

        Args:
            session_id: Session UUID
            role: 'user' or 'assistant'
            content: Message content
            sources: Citation metadata (for assistant messages)

        Returns:
            Created message
        """
        data = {
            "session_id": str(session_id),
            "role": role,
            "content": content,
        }
        if sources:
            data["sources"] = sources

        result = self.client.table(MESSAGES_TABLE).insert(data).execute()

        # Also update session's updated_at
        self.client.table(SESSIONS_TABLE).update(
            {"updated_at": datetime.now().isoformat()}
        ).eq("id", str(session_id)).execute()

        if result.data:
            return ChatMessage(**result.data[0])
        raise Exception("Failed to add message")

    def get_messages(self, session_id: UUID | str) -> list[ChatMessage]:
        """
        Get all messages for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of messages, ordered by creation time
        """
        result = (
            self.client.table(MESSAGES_TABLE)
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at")
            .execute()
        )

        return [ChatMessage(**row) for row in result.data]

    def get_session_with_messages(self, session_id: UUID | str) -> dict | None:
        """
        Get a session with all its messages.
        Convenience method that returns a dict matching the old JSON format.

        Args:
            session_id: Session UUID

        Returns:
            Dict with session data and messages list
        """
        session = self.get_session(session_id)
        if not session:
            return None

        messages = self.get_messages(session_id)

        # Format to match old JSON structure
        return {
            "id": str(session.id),
            "title": session.title,
            "model": session.model,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "sources": m.sources,
                    "timestamp": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ]
        }

    def count_messages(self, session_id: UUID | str) -> int:
        """
        Count messages in a session.

        Args:
            session_id: Session UUID

        Returns:
            Number of messages
        """
        result = (
            self.client.table(MESSAGES_TABLE)
            .select("id", count="exact")
            .eq("session_id", str(session_id))
            .execute()
        )
        return result.count or 0


# Convenience function
def get_chat_repository() -> ChatRepository:
    """Get a ChatRepository instance."""
    return ChatRepository()
