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
        pending = self.store.list_reminders(status=ReminderStatus.PENDING.value)

        for reminder in pending:
            try:
                scheduled_dt = datetime.fromisoformat(reminder.scheduled_time)
                if scheduled_dt <= now:
                    # Deliver notification
                    self.notification_service.notify(
                        title="NOVA Reminder",
                        message=reminder.title,
                    )
                    # Mark triggered/recalculate recurrence in store
                    self.store.mark_triggered(reminder.id)
            except Exception:
                continue


default_scheduler = NOVAScheduler()