import time
import threading
from datetime import datetime
from typing import Optional
from scheduling.reminder_store import ReminderStore, default_reminder_store
from scheduling.reminder_models import ReminderStatus
from services.notification_service import NotificationService, default_notification_service


class NOVAScheduler:
    """
    Background worker thread monitoring pending reminders in ReminderStore.
    Runs non-blocking poll intervals without high CPU usage.
    """

    def __init__(
        self,
        store: Optional[ReminderStore] = None,
        notification_service: Optional[NotificationService] = None,
        poll_interval: float = 2.0,
    ):
        self.store = store or default_reminder_store
        self.notification_service = notification_service or default_notification_service
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts the background scheduler thread if not already running."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Gracefully halts the background scheduler thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run_loop(self) -> None:
        while self._running:
            try:
                self.check_pending_reminders()
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def check_pending_reminders(self) -> None:
        """Inspects store for due reminders and delivers notifications."""
        now = datetime.now()
        
        # Safely fetch pending reminders using string value or Enum
        status_val = (
            ReminderStatus.PENDING.value 
            if hasattr(ReminderStatus.PENDING, "value") 
            else ReminderStatus.PENDING
        )
        pending = self.store.list_reminders(status=status_val)

        for reminder in pending:
            try:
                raw_time = getattr(reminder, "scheduled_time", None)
                if not raw_time:
                    continue

                # Standardize ISO parsing (handles 'Z' suffix if present)
                if isinstance(raw_time, str):
                    clean_time = raw_time.replace("Z", "+00:00")
                    scheduled_dt = datetime.fromisoformat(clean_time)
                elif isinstance(raw_time, datetime):
                    scheduled_dt = raw_time
                else:
                    continue

                # Remove timezone awareness for uniform naive comparison if necessary
                if scheduled_dt.tzinfo is not None:
                    scheduled_dt = scheduled_dt.replace(tzinfo=None)

                if scheduled_dt <= now:
                    title_text = getattr(reminder, "title", "NOVA Reminder")
                    msg_text = getattr(reminder, "user_text", title_text)
                    reminder_id = getattr(reminder, "id", None)

                    # 1. Deliver notification
                    self.notification_service.notify(
                        title="NOVA Reminder",
                        message=title_text or msg_text,
                    )

                    # 2. Mark triggered in store immediately to break duplicate notification loops
                    if reminder_id:
                        if hasattr(self.store, "mark_triggered"):
                            self.store.mark_triggered(reminder_id)
                        elif hasattr(self.store, "update_reminder_status"):
                            self.store.update_reminder_status(reminder_id, "TRIGGERED")
            except Exception:
                # If an error occurs during parsing or delivery for a specific reminder,
                # mark it as triggered or handled to avoid crashing the scheduler loop continuously.
                try:
                    r_id = getattr(reminder, "id", None)
                    if r_id and hasattr(self.store, "mark_triggered"):
                        self.store.mark_triggered(r_id)
                except Exception:
                    pass
                continue


default_scheduler = NOVAScheduler()