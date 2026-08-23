import unittest
import tempfile
from pathlib import Path
from memory.memory_models import SessionData, Message
from memory.memory_store import LocalJSONMemoryStore


class TestMemoryStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) / "test_memory.json"
        self.store = LocalJSONMemoryStore(storage_path=self.temp_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_session(self):
        session = SessionData(session_id="session_1")
        session.messages.append(Message(role="user", content="Hello NOVA"))
        session.messages.append(Message(role="assistant", content="Hello Boss!"))

        self.store.save_session(session)
        loaded = self.store.load_session("session_1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, "session_1")
        self.assertEqual(len(loaded.messages), 2)
        self.assertEqual(loaded.messages[0].content, "Hello NOVA")

    def test_delete_session(self):
        session = SessionData(session_id="session_to_delete")
        self.store.save_session(session)
        self.assertTrue(self.store.delete_session("session_to_delete"))
        self.assertIsNone(self.store.load_session("session_to_delete"))

    def test_clear_all(self):
        self.store.save_session(SessionData(session_id="s1"))
        self.store.save_session(SessionData(session_id="s2"))
        self.store.clear_all()
        self.assertIsNone(self.store.load_session("s1"))
        self.assertIsNone(self.store.load_session("s2"))


if __name__ == "__main__":
    unittest.main()