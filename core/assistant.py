from typing import Optional, Any
from core.llm import OllamaProvider
from core.intent_router import TaskRequest, InputSource, RoutingResult
from core.llm_intent_router import LLMIntentRouter
from core.manager_agent import ManagerAgent
from memory.conversation_memory import ConversationMemory
from scheduling.scheduler import NOVAScheduler, default_scheduler
from context.context_policy import ContextPolicy


class NovaAssistant:
    """
    Main orchestrator for NOVA V2.
    Processes user queries, routes structured intents, delegates to multi-agent manager,
    maintains conversation context, and manages background scheduler lifecycle.
    """

    def __init__(
        self,
        provider: Optional[OllamaProvider] = None,
        llm_router: Optional[LLMIntentRouter] = None,
        manager_agent: Optional[ManagerAgent] = None,
        memory: Optional[ConversationMemory] = None,
        scheduler: Optional[NOVAScheduler] = None,
    ):
        self.provider = provider or OllamaProvider()
        self.llm_router = llm_router or LLMIntentRouter(provider=self.provider)
        self.manager_agent = manager_agent or ManagerAgent()
        self.memory = memory or ConversationMemory()
        self.scheduler = scheduler or default_scheduler

    def initialize(self) -> bool:
        """Verifies health of the underlying LLM provider and boots background scheduler."""
        try:
            self.scheduler.start()
            return self.provider.check_health()
        except Exception:
            return False

    def shutdown(self) -> None:
        """Gracefully stops background services including the scheduler."""
        if hasattr(self, "scheduler") and self.scheduler:
            self.scheduler.stop()

    def process_turn(
        self,
        user_input: str,
        source: InputSource = InputSource.TEXT,
        session_id: str = "default_session",
        tts_engine: Optional[Any] = None,
        **kwargs,
    ) -> str:
        """
        Executes a complete interaction turn:
        1. Records user message in conversation memory
        2. Routes input to structured intent or LLM router
        3. Executes intent via ManagerAgent OR falls back to conversational LLM
        4. Records assistant response in conversation memory
        """
        if not user_input or not user_input.strip():
            return "How can I assist you today, Boss?"

        # 1. Record user turn
        self.memory.add_user_message(session_id=session_id, content=user_input)

        # 2. Intent Routing
        routing_result: RoutingResult = self.llm_router.route(user_input, source=source)

        if routing_result.success and routing_result.task_request:
            # 3a. Delegate structured intent through ManagerAgent with session_id for ContextManager
            mgr_res = self.manager_agent.process_task(
                routing_result.task_request, 
                session_id=session_id
            )
            if mgr_res.success:
                response = str(mgr_res.output)
            else:
                response = f"I couldn't complete that request, Boss: {mgr_res.error}"
        else:
            # 3b. Conversational fallback with sliding memory context & RAG context check
            ctx_request = ContextPolicy.evaluate(
                intent="conversational", 
                query=user_input, 
                session_id=session_id
            )
            ctx_bundle = self.manager_agent.context_manager.build_context(ctx_request)

            history_context = self.memory.get_formatted_context(session_id=session_id)
            rag_context = ctx_bundle.format_rag_context() if ctx_bundle.has_rag_context() else ""

            system_prompt = (
                f"You are NOVA, a helpful offline multi-agent AI assistant for engineering students.\n\n"
                f"Recent Conversation History:\n{history_context}"
            )

            prompt = user_input
            if rag_context:
                prompt += f"\n\n--- RETRIEVED GROUNDING CONTEXT ---\n{rag_context}"

            response = self.provider.generate(prompt=prompt, system_prompt=system_prompt)
            if not response or response.startswith("[!]"):
                response = "I encountered an issue processing that query, Boss."

        # Handle TTS engine invocation for VOICE input when provided
        if source == InputSource.VOICE and tts_engine is not None and hasattr(tts_engine, "speak"):
            tts_engine.speak(response)

        # 4. Record assistant turn
        self.memory.add_assistant_message(session_id=session_id, content=response)
        return response

    # Backward compatibility alias
    process_message = process_turn