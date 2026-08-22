from typing import Dict, List, Optional, Any
from core.tool_definition import Tool, ToolResult, RiskLevel
from core.tools import SystemTools


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Registers a new tool. Raises ValueError if tool name exists."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Retrieves a tool by name."""
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        """Checks if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists metadata for all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "risk_level": t.risk_level.value,
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Executes a registered tool by name with kwargs."""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, output=None, error=f"Unknown tool '{name}'.")
        return tool.execute(**kwargs)


def initialize_default_registry() -> ToolRegistry:
    """Instantiates and registers the baseline Phase 2 tools."""
    registry = ToolRegistry()

    # 1. Open Application Tool
    registry.register(
        Tool(
            name="open_application",
            description="Launches a desktop application by name.",
            func=SystemTools.open_app,
            parameters={"app_name": {"type": "string", "required": True}},
            risk_level=RiskLevel.LOW,
        )
    )

    # 2. Set Volume Tool
    registry.register(
        Tool(
            name="set_volume",
            description="Sets system master audio volume level (0 to 100).",
            func=SystemTools.set_volume,
            parameters={"level": {"type": "integer", "required": True}},
            risk_level=RiskLevel.LOW,
        )
    )

    # 3. Mute Audio Tool
    registry.register(
        Tool(
            name="mute_audio",
            description="Mutes or unmutes system master audio.",
            func=SystemTools.mute_audio,
            parameters={"mute": {"type": "boolean", "required": True}},
            risk_level=RiskLevel.LOW,
        )
    )

    # 4. Take Screenshot Tool
    registry.register(
        Tool(
            name="take_screenshot",
            description="Captures full screen and saves to user Pictures folder.",
            func=SystemTools.take_screenshot,
            parameters={},
            risk_level=RiskLevel.LOW,
        )
    )

    # 5. Create Reminder Tool
    registry.register(
        Tool(
            name="create_reminder",
            description="Schedules a relative countdown reminder alert.",
            func=SystemTools.set_relative_timer,
            parameters={"user_text": {"type": "string", "required": True}},
            risk_level=RiskLevel.LOW,
        )
    )

    return registry


# Global instance reference for easy import across modules
default_registry = initialize_default_registry()