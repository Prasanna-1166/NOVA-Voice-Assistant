from typing import Dict, List, Optional, Any
from core.agent import Agent
from core.intent_router import TaskRequest
from core.productivity_agent import ProductivityAgent
from core.coding_agent import CodingAgent
from core.document_agent import DocumentAgent


INTENT_TO_CAPABILITY_MAP: Dict[str, str] = {
    # System Productivity
    "open_application": "app_management",
    "set_volume": "volume_control",
    "mute_audio": "mute_control",
    "take_screenshot": "screenshot",
    "create_reminder": "reminder_scheduling",
    # Software Engineering / Coding
    "code_generation": "code_generation",
    "code_explanation": "code_explanation",
    "debugging": "debugging",
    "algorithm_help": "algorithm_help",
    "code_conversion": "code_conversion",
    "programming_guidance": "programming_guidance",
    # Document Generation
    "document_generation": "document_generation",
    "report_generation": "report_generation",
    "assignment_generation": "assignment_generation",
    "note_generation": "note_generation",
    "project_documentation": "project_documentation",
    "letter_generation": "letter_generation",
    "resume_generation": "resume_generation",
    "quiz_generation": "quiz_generation",
    "readme_generation": "readme_generation",
}


class AgentRegistry:

    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered.")
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def exists(self, name: str) -> bool:
        return name in self._agents

    def list_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": a.name,
                "description": a.description,
                "capabilities": a.capabilities,
                "allowed_tools": a.allowed_tools,
            }
            for a in self._agents.values()
        ]

    def find_capable_agents(self, task_request: TaskRequest) -> List[Agent]:
        intent = task_request.intent
        required_capability = INTENT_TO_CAPABILITY_MAP.get(intent)

        capable_agents: List[Agent] = []
        for agent in self._agents.values():
            if agent.is_tool_allowed(intent) or (required_capability and required_capability in agent.capabilities):
                capable_agents.append(agent)

        return capable_agents


def initialize_default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(ProductivityAgent())
    registry.register(CodingAgent())
    registry.register(DocumentAgent())
    return registry


default_agent_registry = initialize_default_agent_registry()