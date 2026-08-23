import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Message:
    """Represents an individual conversational turn."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SessionData:
    """Represents a full conversation session context."""

    session_id: str
    messages: list[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        session_id = data.get("session_id", "default")
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=session_id,
            messages=messages,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )