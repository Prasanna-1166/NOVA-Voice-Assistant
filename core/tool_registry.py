from typing import Dict, Optional, Any
from core.tool_definition import ToolDefinition, ToolResult
from core.tools import SystemTools


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        if tool_def.name in self._tools:
            raise ValueError(f"Tool '{tool_def.name}' is already registered.")
        self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}

    def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown tool: '{name}' is not registered in ToolRegistry.",
            )
        try:
            res = tool.execute(**kwargs)
            return ToolResult(success=True, output=res, error=None)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


def initialize_default_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # System Productivity Tools
    registry.register(
        ToolDefinition(
            name="open_application",
            description="Launches a desktop application by name.",
            func=SystemTools.open_application,
            parameters_schema={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="open_app",
            description="Launches a desktop application by name (alias).",
            func=SystemTools.open_application,
            parameters_schema={"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="set_volume",
            description="Sets the master system audio volume level (0-100).",
            func=SystemTools.set_volume,
            parameters_schema={"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="mute_audio",
            description="Mutes or unmutes master system audio.",
            func=SystemTools.mute_audio,
            parameters_schema={"type": "object", "properties": {"mute": {"type": "boolean"}}, "required": ["mute"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="take_screenshot",
            description="Takes a desktop screenshot and saves it locally.",
            func=SystemTools.take_screenshot,
            parameters_schema={"type": "object", "properties": {}},
        )
    )

    # Phase 11 Task Tools
    registry.register(
        ToolDefinition(
            name="create_task",
            description="Creates a new task in the local task store.",
            func=SystemTools.create_task,
            parameters_schema={"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string"}}, "required": ["title"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="list_tasks",
            description="Lists tasks filtered by status.",
            func=SystemTools.list_tasks,
            parameters_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        )
    )

    registry.register(
        ToolDefinition(
            name="complete_task",
            description="Marks a task as completed by identifier or title.",
            func=SystemTools.complete_task,
            parameters_schema={"type": "object", "properties": {"task_identifier": {"type": "string"}}, "required": ["task_identifier"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="update_task",
            description="Updates an existing task.",
            func=SystemTools.update_task,
            parameters_schema={"type": "object", "properties": {"task_identifier": {"type": "string"}, "title": {"type": "string"}, "priority": {"type": "string"}, "status": {"type": "string"}}, "required": ["task_identifier"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="delete_task",
            description="Deletes a task from storage.",
            func=SystemTools.delete_task,
            parameters_schema={"type": "object", "properties": {"task_identifier": {"type": "string"}}, "required": ["task_identifier"]},
        )
    )

    # Phase 11 Preference Tools
    registry.register(
        ToolDefinition(
            name="set_preference",
            description="Sets a persistent user preference key-value pair.",
            func=SystemTools.set_preference,
            parameters_schema={"type": "object", "properties": {"key": {"type": "string"}, "value": {}}, "required": ["key", "value"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="get_preference",
            description="Retrieves a persistent user preference value by key.",
            func=SystemTools.get_preference,
            parameters_schema={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
        )
    )

    # Phase 12 Reminder Tools (SINGLE REGISTRATION)
    registry.register(
        ToolDefinition(
            name="create_reminder",
            description="Schedules a user reminder for a specific time.",
            func=SystemTools.create_reminder,
            parameters_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "scheduled_time": {"type": "string"},
                    "user_text": {"type": "string"},
                    "recurrence": {"type": "string"},
                },
            },
        )
    )
    registry.register(
        ToolDefinition(
            name="list_reminders",
            description="Lists scheduled reminders filtered by status.",
            func=SystemTools.list_reminders,
            parameters_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        )
    )

    registry.register(
        ToolDefinition(
            name="cancel_reminder",
            description="Cancels a scheduled reminder by identifier or title.",
            func=SystemTools.cancel_reminder,
            parameters_schema={"type": "object", "properties": {"identifier": {"type": "string"}}, "required": ["identifier"]},
        )
    )

    registry.register(
        ToolDefinition(
            name="delete_reminder",
            description="Deletes a reminder from storage.",
            func=SystemTools.delete_reminder,
            parameters_schema={"type": "object", "properties": {"identifier": {"type": "string"}}, "required": ["identifier"]},
        )
    )
    # Phase 13 RAG / Document Knowledge Tools
    registry.register(
        ToolDefinition(
            name="ingest_document",
            description="Ingests and indexes a local document (.txt, .md, .pdf, .docx) into the RAG vector store.",
            func=SystemTools.ingest_document,
            parameters_schema={
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
            },
        )
    )

    registry.register(
        ToolDefinition(
            name="query_documents",
            description="Queries indexed local knowledge documents using RAG to answer questions.",
            func=SystemTools.query_documents,
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    )

    registry.register(
        ToolDefinition(
            name="list_knowledge_documents",
            description="Lists all documents currently indexed in the local RAG vector store.",
            func=SystemTools.list_knowledge_documents,
            parameters_schema={"type": "object", "properties": {}},
        )
    )

    return registry

default_registry = initialize_default_registry()
  