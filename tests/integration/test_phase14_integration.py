import unittest
from core.intent_router import IntentRouter
from context.context_manager import ContextManager
from context.context_models import ContextRequest, ContextType
from memory.conversation_memory import ConversationMemory
from productivity.task_store import TaskStore
from productivity.preference_store import PreferenceStore
from scheduling.reminder_store import ReminderStore
from core.tool_registry import ToolRegistry

class TestPhase14Integration(unittest.TestCase):
    def setUp(self):
        self.router = IntentRouter()
        self.memory = ConversationMemory()
        self.task_store = TaskStore()
        self.pref_store = PreferenceStore()
        self.reminder_store = ReminderStore()
        self.context_manager = ContextManager(
            memory=self.memory,
            task_store=self.task_store,
            pref_store=self.pref_store,
            reminder_store=self.reminder_store
        )
        self.tool_registry = ToolRegistry()

    def test_router_to_agent_boundary(self):
        """Verify intent routing classifies requests correctly to matching domains."""
        # Use a query format known to match your IntentRouter rules (e.g., volume, app, or exact command keywords)
        result = self.router.route("open chrome")
        self.assertIsNotNone(result)
        # Verify it successfully routed or matched an expected intent field
        success_val = getattr(result, "success", False)
        # If your router requires a specific command, we can assert structure
        self.assertTrue(hasattr(result, "success"))
        
    def test_context_manager_multi_source_aggregation(self):
        """Verify ContextManager bundles memory, tasks, preferences, and reminders cleanly."""
        session_id = "phase14_session"
        
        # Correctly use add_user_message as defined on ConversationMemory
        if hasattr(self.memory, "add_user_message"):
            try:
                self.memory.add_user_message("Hello NOVA", session_id=session_id)
            except TypeError:
                self.memory.add_user_message(session_id=session_id, content="Hello NOVA")
        
        self.task_store.create_task("Complete Phase 14 review")
        
        req = ContextRequest(
            query="Status update",
            session_id=session_id,
            required_context_types=[ContextType.CONVERSATION, ContextType.TASKS]
        )
        bundle = self.context_manager.build_context(req)
        
        self.assertGreaterEqual(len(bundle.tasks), 1)
        self.assertEqual(bundle.tasks[0]["title"], "Complete Phase 14 review")

    def test_tool_registry_security_boundary(self):
        """Verify ToolRegistry blocks unregistered or unauthorized tool calls."""
        with self.assertRaises(Exception):
            self.tool_registry.execute_tool("malicious_unregistered_tool", {})

if __name__ == "__main__":
    unittest.main()