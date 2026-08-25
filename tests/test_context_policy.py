import unittest
from context.context_policy import ContextPolicy
from context.context_models import ContextType


class TestContextPolicy(unittest.TestCase):
    def test_coding_policy_triggers_rag(self):
        req = ContextPolicy.evaluate(intent="explain_code", query="Explain binary search from my DSA notes")
        self.assertIn(ContextType.RAG, req.required_context_types)

    def test_document_policy_triggers_rag(self):
        req = ContextPolicy.evaluate(intent="generate_document", query="Create notes about deadlocks from my OS PDF")
        self.assertIn(ContextType.RAG, req.required_context_types)


if __name__ == "__main__":
    unittest.main()