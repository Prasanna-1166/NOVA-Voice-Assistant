import unittest
import tempfile
from pathlib import Path
from memory.conversation_memory import ConversationMemory
from memory.memory_store import LocalJSONMemoryStore


class TestConversationMemory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) / "test_conv_memory.json"
        self.store = LocalJSONMemoryStore(storage_path=self.temp_path)
        self.memory = ConversationMemory(store=self.store, max_context_messages=4)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_retrieve_messages(self):
        self.memory.add_user_message("What is Python?")
        self.memory.add_assistant_message("Python is a programming language.")

        msgs = self.memory.get_recent_messages()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].role, "user")
        self.assertEqual(msgs[1].role, "assistant")

    def test_context_window_limit(self):
        for i in range(10):
            self.memory.add_user_message(f"Msg {i}")

        recent = self.memory.get_recent_messages()
        self.assertEqual(len(recent), 4)
        self.assertEqual(recent[-1].content, "Msg 9")

    def test_session_isolation(self):
        self.memory.add_user_message("Session A Msg", session_id="A")
        self.memory.add_user_message("Session B Msg", session_id="B")

        msgs_a = self.memory.get_recent_messages(session_id="A")
        msgs_b = self.memory.get_recent_messages(session_id="B")

        self.assertEqual(len(msgs_a), 1)
        self.assertEqual(msgs_a[0].content, "Session A Msg")
        self.assertEqual(len(msgs_b), 1)
        self.assertEqual(msgs_b[0].content, "Session B Msg")

    def test_formatted_context(self):
        self.memory.add_user_message("Project is ML")
        self.memory.add_assistant_message("Understood")

        ctx = self.memory.get_formatted_context()
        self.assertIn("User: Project is ML", ctx)
        self.assertIn("Assistant: Understood", ctx)


if __name__ == "__main__":
    unittest.main()