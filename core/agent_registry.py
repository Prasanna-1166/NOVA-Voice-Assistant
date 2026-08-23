from typing import Dict, List, Optional, Any
from core.agent import Agent
from core.intent_router import TaskRequest
from core.productivity_agent import ProductivityAgent


# Centralized mapping between Tool Intents and Agent Capabilities
INTENT_TO_CAPABILITY_MAP: Dict[str, str] = {
    "open_application": "app_management",
    "set_volume": "volume_control",
    "mute_audio": "mute_control",
    "take_screenshot": "screenshot",
    "create_reminder": "reminder_scheduling",
}


class AgentRegistry:
    """
    Centralized registry managing specialized agent instances and performing
    deterministic capability matching for TaskRequest routing.
    """

    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Registers a new agent instance. Raises ValueError if agent name exists."""
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered.")
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[Agent]:
        """Retrieves an agent by name."""
        return self._agents.get(name)

    def exists(self, name: str) -> bool:
        """Checks if an agent name is registered."""
        return name in self._agents

    def list_agents(self) -> List[Dict[str, Any]]:
        """Lists metadata for all registered agents."""
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
        """
        Deterministically matches a TaskRequest's intent against agent capabilities
        and allowed tools.
        """
        intent = task_request.intent
        required_capability = INTENT_TO_CAPABILITY_MAP.get(intent)

        capable_agents: List[Agent] = []
        for agent in self._agents.values():
            if agent.is_tool_allowed(intent):
                if required_capability is None or required_capability in agent.capabilities:
                    capable_agents.append(agent)

        return capable_agents


def initialize_default_agent_registry() -> AgentRegistry:
    """Instantiates and registers the baseline Phase 6 agent registry."""
    registry = AgentRegistry()
    registry.register(ProductivityAgent())
    return registry


# Global instance reference for module-level access
default_agent_registry = initialize_default_agent_registry()