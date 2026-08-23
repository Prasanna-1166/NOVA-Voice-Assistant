import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock
from scheduling.reminder_store import ReminderStore
from scheduling.scheduler import NOVAScheduler


class TestScheduler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "reminders.json"
        self.store = ReminderStore(storage_path=self.file_path)
        self.mock_notifier = MagicMock()
        self.scheduler = NOVAScheduler(
            store=self.store,
            notification_service=self.mock_notifier,
            poll_interval=0.1,
        )

    def tearDown(self):
        self.scheduler.stop()
        self.temp_dir.cleanup()

    def test_scheduler_lifecycle(self):
        self.scheduler.start()
        self.assertTrue(self.scheduler._running)
        self.scheduler.stop()
        self.assertFalse(self.scheduler._running)

    def test_due_reminder_triggers_notification(self):
        # Create past/due reminder
        self.store.create_reminder("Due Now", "2020-01-01T00:00:00")
        self.scheduler.check_pending_reminders()
        
        self.mock_notifier.notify.assert_called_once()
        pending = self.store.list_reminders(status="PENDING")
        self.assertEqual(len(pending), 0)

    def test_future_reminder_does_not_trigger(self):
        # Create future reminder
        self.store.create_reminder("Future", "2099-01-01T00:00:00")
        self.scheduler.check_pending_reminders()
        
        self.mock_notifier.notify.assert_not_called()


if __name__ == "__main__":
    unittest.main()