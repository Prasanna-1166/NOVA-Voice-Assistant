from typing import Optional, List
from core.agent import Agent, AgentResult
from core.intent_router import TaskRequest
from core.tool_registry import ToolRegistry, default_registry


class ProductivityAgent(Agent):
    """
    First specialized NOVA agent responsible for system productivity tasks:
    - Application launching
    - Volume and audio control
    - Screen captures
    - Reminders and background timers
    """

    DEFAULT_ALLOWED_TOOLS: List[str] = [
        "open_application",
        "set_volume",
        "mute_audio",
        "take_screenshot",
        "create_reminder",
    ]

    def __init__(
        self,
        name: str = "ProductivityAgent",
        description: str = "Handles local system controls, app launches, screen capture, and relative timers.",
        registry: Optional[ToolRegistry] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            capabilities=[
                "app_management",
                "volume_control",
                "mute_control",
                "screenshot",
                "reminder_scheduling",
            ],
            allowed_tools=self.DEFAULT_ALLOWED_TOOLS,
            registry=registry or default_registry,
        )

    def process_task(self, task_request: TaskRequest) -> AgentResult:
        """
        Validates the task request against allowed capabilities and routes execution
        through the ToolRegistry.
        """
        intent = task_request.intent
        params = task_request.parameters

        if not self.is_tool_allowed(intent):
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"UNAUTHORIZED_TASK: Agent '{self.name}' cannot handle intent '{intent}'.",
            )

        tool_res = self.execute_tool(intent, **params)
        if not tool_res.success:
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"EXECUTION_FAILED: {tool_res.error}",
            )

        return AgentResult(
            success=True,
            output=tool_res.output,
            agent_name=self.name,
            error=None,
        )