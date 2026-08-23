from dataclasses import dataclass
from typing import Optional, Any
from core.agent import Agent, AgentResult
from core.agent_registry import AgentRegistry, default_agent_registry
from core.intent_router import TaskRequest


@dataclass
class ManagerResult:
    """Structured result returned by ManagerAgent orchestration."""
    success: bool
    output: Any
    selected_agent: Optional[str] = None
    agent_result: Optional[AgentResult] = None
    error: Optional[str] = None


class ManagerAgent:
    """
    Central Orchestrator for NOVA V2.
    Receives TaskRequests, queries AgentRegistry for capable agents,
    and delegates task execution. DOES NOT execute tools directly.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or default_agent_registry

    def process_task(self, task_request: Optional[TaskRequest]) -> ManagerResult:
        """
        Orchestrates task execution by delegating to a matched specialized agent.
        """
        if task_request is None:
            return ManagerResult(
                success=False,
                output=None,
                error="INVALID_TASK: TaskRequest object is None.",
            )

        if not task_request.intent or task_request.intent == "unknown":
            return ManagerResult(
                success=False,
                output=None,
                error="UNSUPPORTED_INTENT: TaskRequest contains an empty or unsupported intent.",
            )

        capable_agents = self.registry.find_capable_agents(task_request)
        if not capable_agents:
            return ManagerResult(
                success=False,
                output=None,
                error=f"NO_CAPABLE_AGENT: No registered agent supports intent '{task_request.intent}'.",
            )

        # Deterministic Selection: Choose the first capable agent
        selected_agent: Agent = capable_agents[0]

        agent_result: AgentResult = selected_agent.process_task(task_request)
        if not agent_result.success:
            return ManagerResult(
                success=False,
                output=None,
                selected_agent=selected_agent.name,
                agent_result=agent_result,
                error=f"AGENT_EXECUTION_FAILED: {agent_result.error}",
            )

        return ManagerResult(
            success=True,
            output=agent_result.output,
            selected_agent=selected_agent.name,
            agent_result=agent_result,
            error=None,
        )