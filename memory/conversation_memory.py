import time
from typing import List, Optional

from memory.memory_models import Message, SessionData
from memory.memory_store import MemoryStore, LocalJSONMemoryStore


class ConversationMemory:
    """
    Platform-level Conversation Memory Manager.

    Manages:
    - Short-term conversation context
    - Sliding context window limits
    - Offline persistent memory syncing
    """

    DEFAULT_MAX_CONTEXT_MESSAGES: int = 10

    def __init__(
        self,
        store: Optional[MemoryStore] = None,
        default_session_id: str = "default",
        max_context_messages: int = DEFAULT_MAX_CONTEXT_MESSAGES,
    ):
        self.store = store or LocalJSONMemoryStore()

        self.default_session_id = default_session_id

        self.max_context_messages = max_context_messages

        self._active_sessions: dict[str, SessionData] = {}

    def _get_or_create_session(
        self,
        session_id: str
    ) -> SessionData:
        """
        Return an existing active session or load/create one.
        """

        if session_id not in self._active_sessions:

            loaded = self.store.load_session(session_id)

            if loaded:
                self._active_sessions[session_id] = loaded

            else:
                self._active_sessions[session_id] = (
                    SessionData(
                        session_id=session_id
                    )
                )

        return self._active_sessions[session_id]

    def add_user_message(
        self,
        content: str,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Add a user message to a conversation session.
        """

        sid = (
            session_id
            or self.default_session_id
        )

        session = self._get_or_create_session(sid)

        session.messages.append(
            Message(
                role="user",
                content=content,
            )
        )

        session.updated_at = time.time()

        self.store.save_session(session)

    def add_assistant_message(
        self,
        content: str,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Add an assistant message to a conversation session.
        """

        sid = (
            session_id
            or self.default_session_id
        )

        session = self._get_or_create_session(sid)

        session.messages.append(
            Message(
                role="assistant",
                content=content,
            )
        )

        session.updated_at = time.time()

        self.store.save_session(session)

    def get_recent_messages(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Retrieve the most recent messages for a session.
        """

        sid = (
            session_id
            or self.default_session_id
        )

        session = self._get_or_create_session(sid)

        max_limit = (
            limit
            or self.max_context_messages
        )

        return session.messages[-max_limit:]

    def get_formatted_context(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        Return recent conversation history as
        a human-readable text block.
        """

        messages = self.get_recent_messages(
            session_id,
            limit,
        )

        if not messages:
            return ""

        formatted_turns = []

        for msg in messages:

            role_label = (
                "User"
                if msg.role == "user"
                else "Assistant"
            )

            formatted_turns.append(
                f"{role_label}: {msg.content}"
            )

        return "\n".join(formatted_turns)

    def clear_session(
        self,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Clear an active conversation session and
        remove its persisted data.
        """

        sid = (
            session_id
            or self.default_session_id
        )

        if sid in self._active_sessions:
            del self._active_sessions[sid]

        self.store.delete_session(sid)