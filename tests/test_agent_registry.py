import unittest
from core.agent_registry import AgentRegistry, initialize_default_agent_registry
from core.productivity_agent import ProductivityAgent
from core.coding_agent import CodingAgent
from core.intent_router import TaskRequest, InputSource


class TestAgentRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = AgentRegistry()
        self.prod_agent = ProductivityAgent()
        self.coding_agent = CodingAgent()

    def test_register_and_retrieve_agent(self):
        self.registry.register(self.prod_agent)
        self.assertTrue(self.registry.exists("ProductivityAgent"))

    def test_duplicate_registration_raises(self):
        self.registry.register(self.prod_agent)
        with self.assertRaises(ValueError):
            self.registry.register(self.prod_agent)

    def test_list_agents(self):
        self.registry.register(self.prod_agent)
        self.registry.register(self.coding_agent)
        agents_list = self.registry.list_agents()
        self.assertEqual(len(agents_list), 2)

    def test_find_capable_agents_coding(self):
        self.registry.register(self.prod_agent)
        self.registry.register(self.coding_agent)
        task = TaskRequest(
            intent="code_generation",
            parameters={},
            source=InputSource.TEXT,
        )
        capable = self.registry.find_capable_agents(task)
        self.assertEqual(len(capable), 1)
        self.assertEqual(capable[0].name, "CodingAgent")

    def test_default_agent_registry_initialization(self):
        default_reg = initialize_default_agent_registry()
        self.assertTrue(default_reg.exists("ProductivityAgent"))
        self.assertTrue(default_reg.exists("CodingAgent"))


if __name__ == "__main__":
    unittest.main()