import unittest
from unittest.mock import MagicMock, patch
from core.agent import AgentResult
from core.productivity_agent import ProductivityAgent
from core.intent_router import TaskRequest, InputSource
from core.tool_definition import Tool, ToolResult, RiskLevel
from core.tool_registry import ToolRegistry


class TestProductivityAgent(unittest.TestCase):

    @patch("core.tools.SystemTools.open_app")
    def setUp(self, mock_open_app):
        self.mock_registry = MagicMock(spec=ToolRegistry)
        self.agent = ProductivityAgent(registry=self.mock_registry)

    def test_agent_initialization_and_metadata(self):
        self.assertEqual(self.agent.name, "ProductivityAgent")
        self.assertIn("open_application", self.agent.allowed_tools)
        self.assertIn("set_volume", self.agent.allowed_tools)

    def test_successful_task_processing(self):
        self.mock_registry.exists.return_value = True
        self.mock_registry.execute.return_value = ToolResult(success=True, output="App VS Code opened.")

        task = TaskRequest(
            intent="open_application",
            parameters={"app_name": "vscode"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertTrue(res.success)
        self.assertEqual(res.agent_name, "ProductivityAgent")
        self.assertEqual(res.output, "App VS Code opened.")
        self.mock_registry.execute.assert_called_once_with("open_application", app_name="vscode")

    def test_unauthorized_tool_rejection(self):
        task = TaskRequest(
            intent="unauthorized_system_format",
            parameters={},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("UNAUTHORIZED_TASK", res.error)
        self.mock_registry.execute.assert_not_called()

    def test_unregistered_tool_handling(self):
        self.mock_registry.exists.return_value = False

        task = TaskRequest(
            intent="open_application",
            parameters={"app_name": "vscode"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("REGISTRY_ERROR", res.error)

    def test_tool_execution_failure_encapsulation(self):
        self.mock_registry.exists.return_value = True
        self.mock_registry.execute.return_value = ToolResult(success=False, output=None, error="Launch failed")

        task = TaskRequest(
            intent="open_application",
            parameters={"app_name": "invalid_app"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("EXECUTION_FAILED", res.error)


if __name__ == "__main__":
    unittest.main()