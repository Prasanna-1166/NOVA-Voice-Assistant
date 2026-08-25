import unittest

from context.context_models import ContextRequest, ContextType
from context.context_manager import ContextManager
from memory.conversation_memory import ConversationMemory
from productivity.task_store import TaskStore
from productivity.preference_store import PreferenceStore
from scheduling.reminder_store import ReminderStore


class TestContextManager(unittest.TestCase):

    def setUp(self):
        self.memory = ConversationMemory()
        self.task_store = TaskStore()

        # Clean existing persistent pending tasks
        for task in self.task_store.list_tasks(status="PENDING"):
            self.task_store.delete_task(task.id)

        self.pref_store = PreferenceStore()
        self.reminder_store = ReminderStore()

        self.cm = ContextManager(
            memory=self.memory,
            task_store=self.task_store,
            pref_store=self.pref_store,
            reminder_store=self.reminder_store,
        )

    def test_conversation_context_retrieval(self):
        session_id = "test_session_cm"

        # Add a single message to conversation memory.
        if hasattr(self.memory, "add_message"):
            self.memory.add_message(
                session_id,
                "user",
                "Hello NOVA"
            )

        elif hasattr(self.memory, "add_user_message"):
            try:
                self.memory.add_user_message(
                    content="Hello NOVA",
                    session_id=session_id
                )
            except TypeError:
                self.memory.add_user_message(
                    session_id=session_id,
                    content="Hello NOVA"
                )

        else:
            self.fail(
                "ConversationMemory does not provide a supported "
                "method for adding a user message."
            )

        # Request conversation context.
        request = ContextRequest(
            query="Hello",
            session_id=session_id,
            required_context_types=[
                ContextType.CONVERSATION
            ],
        )

        # Build context.
        bundle = self.cm.build_context(request)

        # Verify conversation context was retrieved.
        self.assertGreaterEqual(
            len(bundle.conversation_context),
            1
        )

        self.assertEqual(
            bundle.conversation_context[0]["content"],
            "Hello NOVA"
        )


if __name__ == "__main__":
    unittest.main()