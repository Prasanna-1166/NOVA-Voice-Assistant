import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from scheduling.reminder_models import Reminder, ReminderStatus, RecurrenceType


class ReminderStore:
    """
    Offline JSON persistence layer for NOVA scheduled reminders.
    Stores reminders in Path.home() / "Documents" / "NOVA" / "reminders.json".
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            base_dir = Path.home() / "Documents" / "NOVA"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.file_path = base_dir / "reminders.json"
        else:
            self.file_path = storage_path
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self._save_all([])

    def _load_all(self) -> List[Reminder]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Reminder.from_dict(item) for item in data]
        except Exception:
            return []

    def _save_all(self, reminders: List[Reminder]) -> None:
        raw_data = [r.to_dict() for r in reminders]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=2)

    def create_reminder(
        self,
        title: str,
        scheduled_time: str,
        recurrence: str = "NONE",
    ) -> Reminder:
        if not title or not title.strip():
            raise ValueError("Reminder title cannot be empty.")

        reminders = self._load_all()
        rec_enum = RecurrenceType.NONE
        try:
            rec_enum = RecurrenceType(recurrence.upper())
        except ValueError:
            rec_enum = RecurrenceType.NONE

        reminder = Reminder(
            title=title.strip(),
            scheduled_time=scheduled_time,
            recurrence=rec_enum,
        )
        reminders.append(reminder)
        self._save_all(reminders)
        return reminder

    def get_reminder(self, identifier: str) -> Optional[Reminder]:
        reminders = self._load_all()
        clean_id = identifier.lower().strip()
        for r in reminders:
            if r.id.lower() == clean_id or r.title.lower() == clean_id:
                return r
        return None

    def list_reminders(self, status: Optional[str] = None) -> List[Reminder]:
        reminders = self._load_all()
        if status:
            clean_status = status.upper().strip()
            return [r for r in reminders if r.status.value == clean_status]
        return reminders

    def cancel_reminder(self, identifier: str) -> Optional[Reminder]:
        reminders = self._load_all()
        target = None
        clean_id = identifier.lower().strip()
        for r in reminders:
            if (r.id.lower() == clean_id or clean_id in r.title.lower()) and r.status == ReminderStatus.PENDING:
                r.status = ReminderStatus.CANCELLED
                target = r
                break
        if target:
            self._save_all(reminders)
        return target

    def delete_reminder(self, identifier: str) -> bool:
        reminders = self._load_all()
        clean_id = identifier.lower().strip()
        filtered = [r for r in reminders if r.id.lower() != clean_id and clean_id not in r.title.lower()]
        if len(filtered) < len(reminders):
            self._save_all(filtered)
            return True
        return False

    def mark_triggered(self, identifier: str) -> Optional[Reminder]:
        reminders = self._load_all()
        target = None
        for r in reminders:
            if r.id == identifier:
                if r.recurrence == RecurrenceType.DAILY:
                    dt = datetime.fromisoformat(r.scheduled_time) + timedelta(days=1)
                    r.scheduled_time = dt.isoformat()
                    r.status = ReminderStatus.PENDING
                elif r.recurrence == RecurrenceType.WEEKLY:
                    dt = datetime.fromisoformat(r.scheduled_time) + timedelta(weeks=1)
                    r.scheduled_time = dt.isoformat()
                    r.status = ReminderStatus.PENDING
                else:
                    r.status = ReminderStatus.TRIGGERED
                target = r
                break
        if target:
            self._save_all(reminders)
        return target


default_reminder_store = ReminderStore()