import unittest
import tempfile
from pathlib import Path
from scheduling.reminder_store import ReminderStore
from scheduling.reminder_models import ReminderStatus, RecurrenceType


class TestReminderStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "reminders.json"
        self.store = ReminderStore(storage_path=self.file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_get_reminder(self):
        rem = self.store.create_reminder("Submit OS Assignment", "2026-08-25T18:00:00")
        self.assertEqual(rem.title, "Submit OS Assignment")
        self.assertEqual(rem.status, ReminderStatus.PENDING)

        retrieved = self.store.get_reminder(rem.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Submit OS Assignment")

    def test_list_reminders_filtering(self):
        self.store.create_reminder("Task A", "2026-08-25T18:00:00")
        self.store.create_reminder("Task B", "2026-08-25T19:00:00")
        
        pending = self.store.list_reminders(status="PENDING")
        self.assertEqual(len(pending), 2)

    def test_cancel_reminder(self):
        rem = self.store.create_reminder("Revise Python", "2026-08-25T20:00:00")
        cancelled = self.store.cancel_reminder(rem.id)
        self.assertIsNotNone(cancelled)
        self.assertEqual(cancelled.status, ReminderStatus.CANCELLED)

    def test_delete_reminder(self):
        rem = self.store.create_reminder("Delete Me", "2026-08-25T20:00:00")
        success = self.store.delete_reminder(rem.id)
        self.assertTrue(success)
        self.assertIsNone(self.store.get_reminder(rem.id))

    def test_mark_triggered(self):
        rem = self.store.create_reminder("Trigger Test", "2026-08-25T20:00:00")
        triggered = self.store.mark_triggered(rem.id)
        self.assertEqual(triggered.status, ReminderStatus.TRIGGERED)

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            self.store.create_reminder("", "2026-08-25T20:00:00")


if __name__ == "__main__":
    unittest.main()