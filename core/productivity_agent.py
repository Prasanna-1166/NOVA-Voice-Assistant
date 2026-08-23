from typing import List, Optional
from core.agent import Agent, AgentResult
from core.intent_router import TaskRequest
from core.tool_registry import ToolRegistry, default_registry


class ProductivityAgent(Agent):
    """
    Specialized Agent for system productivity automation, task management, user preferences, and reminders.
    Delegates all tool calls strictly through the ToolRegistry execution boundary.
    """

    DEFAULT_ALLOWED_TOOLS: List[str] = [
        "open_application",
        "open_app",
        "set_volume",
        "mute_audio",
        "take_screenshot",
        "create_reminder",
        "list_reminders",
        "cancel_reminder",
        "delete_reminder",
        "create_task",
        "list_tasks",
        "complete_task",
        "update_task",
        "delete_task",
        "set_preference",
        "get_preference",
    ]

    def __init__(
        self,
        name: str = "ProductivityAgent",
        description: str = "Specialized AI agent for OS-level productivity, desktop automation, task management, user preferences, and reminders.",
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
                "create_reminder",
                "list_reminders",
                "cancel_reminder",
                "delete_reminder",
                "task_management",
                "todo_management",
                "preference_management",
            ],
            allowed_tools=self.DEFAULT_ALLOWED_TOOLS,
            registry=registry or default_registry,
        )

    def process_task(self, task_request: TaskRequest) -> AgentResult:
        intent = task_request.intent
        parameters = task_request.parameters or {}

        if not self.is_tool_allowed(intent):
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"UNAUTHORIZED_TASK: Tool '{intent}' is not authorized for {self.name}.",
            )

        if not self.registry.exists(intent):
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"REGISTRY_ERROR: Tool '{intent}' is not registered in ToolRegistry.",
            )

        tool_res = self.execute_tool(intent, **parameters)
        if tool_res.success:
            return AgentResult(
                success=True,
                output=tool_res.output,
                agent_name=self.name,
                error=None,
            )
        else:
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"EXECUTION_FAILED: {tool_res.error}",
            )