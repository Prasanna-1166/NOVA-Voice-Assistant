import unittest
import tempfile
from pathlib import Path
from productivity.task_store import TaskStore
from productivity.task_models import TaskStatus, TaskPriority


class TestTaskStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) / "test_tasks.json"
        self.store = TaskStore(storage_path=self.temp_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_get_task(self):
        task = self.store.create_task(title="DSA Assignment", priority="HIGH")
        self.assertEqual(task.title, "DSA Assignment")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.status, TaskStatus.PENDING)

        fetched = self.store.get_task(task.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "DSA Assignment")

    def test_complete_task(self):
        task = self.store.create_task(title="ML Report")
        completed = self.store.complete_task(task.id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(completed.completed_at)

    def test_list_tasks_filtering(self):
        self.store.create_task(title="Task 1")
        t2 = self.store.create_task(title="Task 2")
        self.store.complete_task(t2.id)

        pending = self.store.list_pending_tasks()
        completed = self.store.list_completed_tasks()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].title, "Task 1")
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].title, "Task 2")

    def test_delete_task(self):
        task = self.store.create_task(title="Task to delete")
        self.assertTrue(self.store.delete_task(task.id))
        self.assertIsNone(self.store.get_task(task.id))

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            self.store.create_task(title="   ")


if __name__ == "__main__":
    unittest.main()