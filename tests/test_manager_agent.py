import unittest
from unittest.mock import MagicMock, patch
from core.manager_agent import ManagerAgent
from core.agent_registry import AgentRegistry
from core.productivity_agent import ProductivityAgent
from core.intent_router import TaskRequest, InputSource


class TestManagerAgent(unittest.TestCase):

    def setUp(self):
        self.registry = AgentRegistry()
        self.prod_agent = ProductivityAgent()
        self.registry.register(self.prod_agent)
        self.manager = ManagerAgent(registry=self.registry)

    @patch("os.system")
    def test_open_application_delegation(self, mock_os_system):
        task = TaskRequest(
            intent="open_application",
            parameters={"app_name": "vscode"},
            source=InputSource.TEXT,
        )
        res = self.manager.process_task(task)
        self.assertTrue(res.success)
        self.assertEqual(res.selected_agent, "ProductivityAgent")

    @patch("core.tools.SystemTools.set_volume")
    def test_set_volume_delegation(self, mock_set_vol):
        mock_set_vol.return_value = "Volume set to 50"
        task = TaskRequest(
            intent="set_volume",
            parameters={"level": 50},
            source=InputSource.TEXT,
        )
        res = self.manager.process_task(task)
        self.assertTrue(res.success)
        self.assertEqual(res.selected_agent, "ProductivityAgent")

    def test_none_task_request_handling(self):
        res = self.manager.process_task(None)
        self.assertFalse(res.success)
        self.assertIn("INVALID_TASK", res.error)

    def test_unsupported_intent_handling(self):
        task = TaskRequest(
            intent="unknown",
            parameters={},
            source=InputSource.TEXT,
        )
        res = self.manager.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("UNSUPPORTED_INTENT", res.error)

    def test_no_capable_agent_handling(self):
        task = TaskRequest(
            intent="unsupported_coding_intent",
            parameters={},
            source=InputSource.TEXT,
        )
        res = self.manager.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("NO_CAPABLE_AGENT", res.error)

    def test_end_to_end_orchestration_flow(self):
        mock_agent = MagicMock()
        mock_agent.name = "MockAgent"
        mock_agent.is_tool_allowed.return_value = True
        mock_agent.capabilities = ["app_management"]
        mock_agent.process_task.return_value = MagicMock(
            success=True, output="Mock Execution OK", agent_name="MockAgent", error=None
        )

        custom_registry = AgentRegistry()
        custom_registry.register(mock_agent)
        manager = ManagerAgent(registry=custom_registry)

        task = TaskRequest(
            intent="open_application",
            parameters={"app_name": "notepad"},
            source=InputSource.TEXT,
        )
        res = manager.process_task(task)

        self.assertTrue(res.success)
        self.assertEqual(res.selected_agent, "MockAgent")
        self.assertEqual(res.output, "Mock Execution OK")
        mock_agent.process_task.assert_called_once_with(task)


if __name__ == "__main__":
    unittest.main()