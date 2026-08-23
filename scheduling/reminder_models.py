# scheduling/reminder_models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    TRIGGERED = "TRIGGERED"
    CANCELLED = "CANCELLED"


class RecurrenceType(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


@dataclass
class Reminder:
    title: str
    scheduled_time: str  # ISO 8601 string: YYYY-MM-DDTHH:MM:SS
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: ReminderStatus = ReminderStatus.PENDING
    recurrence: RecurrenceType = RecurrenceType.NONE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "scheduled_time": self.scheduled_time,
            "status": self.status.value if isinstance(self.status, ReminderStatus) else self.status,
            "recurrence": self.recurrence.value if isinstance(self.recurrence, RecurrenceType) else self.recurrence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            scheduled_time=data.get("scheduled_time", ""),
            status=ReminderStatus(data.get("status", ReminderStatus.PENDING.value)),
            recurrence=RecurrenceType(data.get("recurrence", RecurrenceType.NONE.value)),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )