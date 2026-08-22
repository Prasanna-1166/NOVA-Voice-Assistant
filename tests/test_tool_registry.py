import unittest
from core.tool_definition import Tool, ToolResult, RiskLevel
from core.tool_registry import ToolRegistry, initialize_default_registry


class TestToolRegistry(unittest.TestCase):

    def test_tool_registration(self):
        registry = ToolRegistry()
        dummy_tool = Tool(
            name="test_tool",
            description="A test tool.",
            func=lambda x: f"hello {x}",
            parameters={"x": {"type": "string"}},
            risk_level=RiskLevel.LOW,
        )
        registry.register(dummy_tool)
        self.assertTrue(registry.exists("test_tool"))
        self.assertEqual(registry.get("test_tool"), dummy_tool)

    def test_duplicate_registration_raises(self):
        registry = ToolRegistry()
        dummy_tool = Tool(
            name="test_tool",
            description="A test tool.",
            func=lambda: "ok",
            parameters={},
        )
        registry.register(dummy_tool)
        with self.assertRaises(ValueError):
            registry.register(dummy_tool)

    def test_tool_execution_success(self):
        registry = ToolRegistry()
        dummy_tool = Tool(
            name="add_numbers",
            description="Adds two numbers.",
            func=lambda a, b: a + b,
            parameters={"a": {"type": "int"}, "b": {"type": "int"}},
        )
        registry.register(dummy_tool)
        res = registry.execute("add_numbers", a=5, b=10)
        self.assertTrue(res.success)
        self.assertEqual(res.output, 15)
        self.assertIsNone(res.error)

    def test_unknown_tool_execution(self):
        registry = ToolRegistry()
        res = registry.execute("non_existent_tool")
        self.assertFalse(res.success)
        self.assertIn("Unknown tool", res.error)

    def test_default_registry_initialization(self):
        registry = initialize_default_registry()
        tools = ["open_application", "set_volume", "mute_audio", "take_screenshot", "create_reminder"]
        for t in tools:
            self.assertTrue(registry.exists(t))


if __name__ == "__main__":
    unittest.main()