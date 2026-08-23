import logging
from typing import Tuple, Optional
from core.llm import OllamaProvider
from core.intent_router import IntentRouter, InputSource, TaskRequest
from core.llm_intent_router import LLMIntentRouter
from core.manager_agent import ManagerAgent, ManagerResult
from core.agent_registry import default_agent_registry
from core.tool_registry import default_registry
from core.tools import SystemTools

logger = logging.getLogger(__name__)


class NovaAssistant:
    """
    Core Runtime Orchestration Engine for NOVA V2.
    Routes user inputs through Deterministic Router -> LLM Router -> ManagerAgent -> Specialized Agent -> ToolRegistry.
    Falls back gracefully to conversational LLM response for non-tool queries.
    """

    def __init__(
        self,
        provider: Optional[OllamaProvider] = None,
        manager: Optional[ManagerAgent] = None,
    ):
        self.provider = provider or OllamaProvider()
        self.manager = manager or ManagerAgent(registry=default_agent_registry)
        self.llm_router = LLMIntentRouter(provider=self.provider, registry=default_registry)
        self.deterministic_router = IntentRouter()

    def process_message(
        self,
        user_input: str,
        source: InputSource = InputSource.TEXT,
        tts_engine=None,
    ) -> str:
        """
        Main entry point for both Terminal (TEXT) and Voice (VOICE) inputs.
        """
        clean_input = user_input.strip()
        if not clean_input:
            return "I didn't receive any input, Boss."

        # Step 1: Route Intent (Deterministic First -> LLM Fallback)
        routing_res = self.llm_router.route(clean_input, source=source)

        # Step 2: If Intent Routing Succeeded into a TaskRequest -> Execute via ManagerAgent Pipeline
        if routing_res.success and routing_res.task_request:
            manager_res: ManagerResult = self.manager.process_task(routing_res.task_request)
            if manager_res.success:
                response_text = str(manager_res.output)
                if source == InputSource.VOICE and tts_engine:
                    tts_engine.speak(response_text)
                return response_text
            else:
                error_msg = f"Task execution encountered an error: {manager_res.error}"
                if source == InputSource.VOICE and tts_engine:
                    tts_engine.speak("Sorry Boss, I couldn't complete that task.")
                return error_msg

        # Step 3: Check Legacy SystemTools Command Processors (for non-migrated capabilities like Word Docs, WhatsApp, YouTube)
        is_handled, legacy_response = SystemTools.process_command(clean_input, tts_engine=tts_engine, assistant_engine=self)
        if is_handled:
            if source == InputSource.VOICE and tts_engine and legacy_response:
                tts_engine.speak(legacy_response)
            return legacy_response

        # Step 4: Conversational Fallback (General Q&A / Knowledge queries like "Explain deadlock")
        system_prompt = (
            "You are SWEETY, an intelligent local AI assistant for engineering students. "
            "Keep responses concise, clear, and direct."
        )
        llm_response = self.provider.generate(prompt=clean_input, system_prompt=system_prompt)

        if not llm_response or llm_response.startswith("[!]"):
            fallback_text = "I'm having trouble connecting to my local LLM engine, Boss."
            if source == InputSource.VOICE and tts_engine:
                tts_engine.speak(fallback_text)
            return fallback_text

        if source == InputSource.VOICE and tts_engine:
            tts_engine.speak(llm_response)

        return llm_response