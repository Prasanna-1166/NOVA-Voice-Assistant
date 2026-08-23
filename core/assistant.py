import logging
from typing import Optional
from core.llm import OllamaProvider
from core.intent_router import IntentRouter, InputSource
from core.llm_intent_router import LLMIntentRouter
from core.manager_agent import ManagerAgent, ManagerResult
from core.agent_registry import default_agent_registry
from core.tool_registry import default_registry
from core.tools import SystemTools
from memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class NovaAssistant:
    """
    Core Runtime Orchestration Engine for NOVA V2.
    Integrates Platform Conversation Memory with Intent Routing & Multi-Agent Delegation.
    """

    def __init__(
        self,
        provider: Optional[OllamaProvider] = None,
        manager: Optional[ManagerAgent] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        self.provider = provider or OllamaProvider()
        self.manager = manager or ManagerAgent(registry=default_agent_registry)
        self.memory = memory or ConversationMemory()
        self.llm_router = LLMIntentRouter(provider=self.provider, registry=default_registry)
        self.deterministic_router = IntentRouter()

    def process_message(
        self,
        user_input: str,
        source: InputSource = InputSource.TEXT,
        tts_engine=None,
        session_id: str = "default",
    ) -> str:
        clean_input = user_input.strip()
        if not clean_input:
            return "I didn't receive any input, Boss."

        # Step 1: Record User Input in Memory
        self.memory.add_user_message(clean_input, session_id=session_id)

        # Step 2: Route Intent
        routing_res = self.llm_router.route(clean_input, source=source)

        # Step 3: Executable Task Request Path
        if routing_res.success and routing_res.task_request:
            manager_res: ManagerResult = self.manager.process_task(routing_res.task_request)
            if manager_res.success:
                response_text = str(manager_res.output)
            else:
                response_text = f"Task execution encountered an error: {manager_res.error}"

            self.memory.add_assistant_message(response_text, session_id=session_id)
            if source == InputSource.VOICE and tts_engine:
                tts_engine.speak(response_text)
            return response_text

        # Step 4: Legacy System Tools Command Fallback
        is_handled, legacy_response = SystemTools.process_command(clean_input, tts_engine=tts_engine, assistant_engine=self)
        if is_handled:
            self.memory.add_assistant_message(legacy_response, session_id=session_id)
            if source == InputSource.VOICE and tts_engine and legacy_response:
                tts_engine.speak(legacy_response)
            return legacy_response

        # Step 5: Conversational Fallback with Context Window
        conversation_context = self.memory.get_formatted_context(session_id=session_id)
        system_prompt = (
            "You are SWEETY, an intelligent local AI assistant for engineering students.\n"
            "Keep responses concise, clear, and direct.\n\n"
            f"Recent Conversation History:\n{conversation_context}"
        )

        llm_response = self.provider.generate(prompt=clean_input, system_prompt=system_prompt)

        if not llm_response or llm_response.startswith("[!]"):
            fallback_text = "I'm having trouble connecting to my local LLM engine, Boss."
            self.memory.add_assistant_message(fallback_text, session_id=session_id)
            if source == InputSource.VOICE and tts_engine:
                tts_engine.speak(fallback_text)
            return fallback_text

        self.memory.add_assistant_message(llm_response, session_id=session_id)
        if source == InputSource.VOICE and tts_engine:
            tts_engine.speak(llm_response)

        return llm_response