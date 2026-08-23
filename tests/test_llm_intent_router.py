import unittest
from unittest.mock import MagicMock
from core.llm_intent_router import LLMIntentRouter
from core.intent_router import InputSource
from core.tool_registry import initialize_default_registry


class TestLLMIntentRouter(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MagicMock()
        self.registry = initialize_default_registry()
        self.router = LLMIntentRouter(provider=self.mock_provider, registry=self.registry)

    def test_deterministic_priority(self):
        """Deterministic queries should not trigger Ollama calls."""
        res = self.router.route("open vscode")
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "open_application")
        self.mock_provider.generate.assert_not_called()

    def test_llm_valid_json_routing(self):
        """Ambiguous query delegates to LLM and parses valid JSON."""
        self.mock_provider.generate.return_value = '{"intent": "open_application", "parameters": {"app_name": "vscode"}}'
        res = self.router.route("Could you launch my primary coding editor?")
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "open_application")
        self.assertEqual(res.task_request.parameters["app_name"], "vscode")
        self.mock_provider.generate.assert_called_once()

    def test_markdown_wrapped_json_parsing(self):
        """Handles Markdown backtick wrapped JSON from LLM outputs."""
        self.mock_provider.generate.return_value = '```json\n{"intent": "set_volume", "parameters": {"level": 40}}\n```'
        res = self.router.route("Please set volume to 40 percent")
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "set_volume")
        self.assertEqual(res.task_request.parameters["level"], 40)

    def test_unregistered_tool_rejection(self):
        """Rejects hallucinated/unregistered tools."""
        self.mock_provider.generate.return_value = '{"intent": "delete_system_files", "parameters": {}}'
        res = self.router.route("Delete my system files")
        self.assertFalse(res.success)
        self.assertIn("not registered", res.error)

    def test_invalid_parameter_rejection(self):
        """Rejects out-of-bounds parameters."""
        self.mock_provider.generate.return_value = '{"intent": "set_volume", "parameters": {"level": 150}}'
        res = self.router.route("Set volume to 150")
        self.assertFalse(res.success)
        self.assertIn("INVALID_PARAMS", res.error)

    def test_conversational_unknown_rejection(self):
        """General questions return unknown rejection without tool calls."""
        self.mock_provider.generate.return_value = '{"intent": "unknown", "parameters": {}}'
        res = self.router.route("Explain deadlock in operating systems")
        self.assertFalse(res.success)
        self.assertIn("UNSUPPORTED", res.error)


if __name__ == "__main__":
    unittest.main()