import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class Task:
    """Represents a structured to-do / task item."""

    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    due_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "due_at": self.due_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        status_raw = data.get("status", "PENDING")
        try:
            status = TaskStatus(status_raw)
        except ValueError:
            status = TaskStatus.PENDING

        priority_raw = data.get("priority", "MEDIUM")
        try:
            priority = TaskPriority(priority_raw)
        except ValueError:
            priority = TaskPriority.MEDIUM

        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", "Untitled Task"),
            description=data.get("description", ""),
            status=status,
            priority=priority,
            created_at=data.get("created_at", time.time()),
            completed_at=data.get("completed_at"),
            due_at=data.get("due_at"),
            metadata=data.get("metadata", {}),
        )