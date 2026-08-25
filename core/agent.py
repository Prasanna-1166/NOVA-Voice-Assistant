from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any
from core.intent_router import TaskRequest
from core.tool_definition import ToolResult
from core.tool_registry import ToolRegistry, default_registry


@dataclass
class AgentResult:
    """Structured output returned by an Agent execution."""
    success: bool
    output: Any
    agent_name: str
    error: Optional[str] = None


class Agent(ABC):
    """
    Abstract Base Class for all specialized NOVA V2 Agents.
    Enforces tool access restrictions and tool execution boundaries.
    """

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        allowed_tools: List[str],
        registry: Optional[ToolRegistry] = None,
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.allowed_tools = allowed_tools
        self.registry = registry if registry is not None else default_registry

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Checks if a tool is explicitly authorized for this agent."""
        return tool_name in self.allowed_tools

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Executes a tool through the ToolRegistry boundary, strictly enforcing tool permissions.
        """
        if not self.is_tool_allowed(tool_name):
            return ToolResult(
                success=False,
                output=None,
                error=f"UNAUTHORIZED_TASK: Tool '{tool_name}' is not authorized for {self.name}.",
            )

        if not self.registry.exists(tool_name):
            return ToolResult(
                success=False,
                output=None,
                error=f"REGISTRY_ERROR: Tool '{tool_name}' is not registered in ToolRegistry.",
            )

        return self.registry.execute(tool_name, **kwargs)

    @abstractmethod
    def process_task(
        self, 
        task_request: TaskRequest, 
        context: Optional[Any] = None
    ) -> AgentResult:
        """Processes a structured TaskRequest with optional context bundle and returns an AgentResult."""
        pass