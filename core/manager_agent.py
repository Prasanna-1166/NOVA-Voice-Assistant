from dataclasses import dataclass
from typing import Optional, Any
from core.agent import Agent, AgentResult
from core.agent_registry import AgentRegistry, default_agent_registry
from core.intent_router import TaskRequest
from context.context_policy import ContextPolicy
from context.context_manager import ContextManager


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
    Receives TaskRequests, builds a ContextBundle via ContextManager,
    queries AgentRegistry for capable agents, and delegates task execution.
    DOES NOT execute tools directly.
    """

    def __init__(
        self, 
        registry: Optional[AgentRegistry] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.registry = registry or default_agent_registry
        self.context_manager = context_manager or ContextManager()

    def process_task(
        self, 
        task_request: Optional[TaskRequest], 
        session_id: str = "default_session"
    ) -> ManagerResult:
        """
        Orchestrates task execution by building relevant context and delegating
        to a matched specialized agent.
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

        # Select capable agent
        selected_agent: Agent = capable_agents[0]

        # Evaluate Context Policy and Build Context Bundle
        query_text = getattr(task_request, "original_input", "") or str(task_request.parameters)
        ctx_request = ContextPolicy.evaluate(
            intent=task_request.intent,
            query=query_text,
            session_id=session_id,
        )
        context_bundle = self.context_manager.build_context(ctx_request)

        # Delegate to specialized agent with Context Bundle
        agent_result: AgentResult = selected_agent.process_task(
            task_request, 
            context=context_bundle
        )

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