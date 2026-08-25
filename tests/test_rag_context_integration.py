import unittest
from context.context_models import ContextBundle
from core.coding_agent import CodingAgent
from core.intent_router import TaskRequest


class TestRAGContextIntegration(unittest.TestCase):
    def test_coding_agent_handles_rag_context_without_execution(self):
        agent = CodingAgent()
        bundle = ContextBundle(query="explain code")
        req = TaskRequest(intent="explain_code", parameters={}, original_input="Explain binary search")
        res = agent.process_task(req, context=bundle)
        self.assertTrue(res.success)


if __name__ == "__main__":
    unittest.main()