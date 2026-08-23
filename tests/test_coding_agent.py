import unittest
from unittest.mock import MagicMock
from core.coding_agent import CodingAgent
from core.intent_router import TaskRequest, InputSource


class TestCodingAgent(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MagicMock()
        self.agent = CodingAgent(provider=self.mock_provider)

    def test_coding_agent_metadata(self):
        self.assertEqual(self.agent.name, "CodingAgent")
        self.assertIn("code_generation", self.agent.capabilities)
        self.assertIn("debugging", self.agent.capabilities)
        self.assertEqual(self.agent.allowed_tools, [])

    def test_successful_code_generation_task(self):
        self.mock_provider.generate.return_value = "```python\ndef binary_search(): pass\n```"
        task = TaskRequest(
            intent="code_generation",
            parameters={},
            source=InputSource.TEXT,
            original_input="Write Python code for binary search",
        )

        res = self.agent.process_task(task)
        self.assertTrue(res.success)
        self.assertEqual(res.agent_name, "CodingAgent")
        self.assertIn("binary_search", res.output)
        self.mock_provider.generate.assert_called_once()

    def test_empty_query_handling(self):
        task = TaskRequest(
            intent="code_generation",
            parameters={},
            source=InputSource.TEXT,
            original_input="",
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("EMPTY_QUERY", res.error)
        self.mock_provider.generate.assert_not_called()

    def test_provider_failure_handling(self):
        self.mock_provider.generate.return_value = "[!] Generation timed out."
        task = TaskRequest(
            intent="debugging",
            parameters={},
            source=InputSource.TEXT,
            original_input="Fix this code",
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("LLM_GENERATION_FAILED", res.error)


if __name__ == "__main__":
    unittest.main()