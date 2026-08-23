import json
import re
from typing import Dict, Any, Optional
from core.intent_router import TaskRequest, InputSource, RoutingResult, IntentRouter
from core.llm import OllamaProvider
from core.tool_registry import ToolRegistry, default_registry


SYSTEM_ROUTER_PROMPT = """You are NOVA's intent classification engine.
Your sole responsibility is to analyze the user input and map it to a supported tool intent.

Supported Intents & Parameter Schemas:
1. "open_application" -> parameters: {"app_name": "<string>"}
2. "set_volume" -> parameters: {"level": <integer 0-100>}
3. "mute_audio" -> parameters: {"mute": <boolean>}
4. "take_screenshot" -> parameters: {}
5. "create_reminder" -> parameters: {"user_text": "<string>"}

Rules:
- Respond strictly with a single valid JSON object.
- Never output Markdown code blocks, explanations, prose, or code.
- If the request does not cleanly map to one of the 5 supported intents above, return: {"intent": "unknown", "parameters": {}}
- Do not invent new tools or parameters.

Example Output:
{"intent": "open_application", "parameters": {"app_name": "vscode"}}
"""


class LLMIntentRouter:
    """
    LLM-assisted Intent Router using OllamaProvider (qwen2.5:3b).
    Parses natural language requests into structured TaskRequests.
    Performs multi-stage JSON parsing and strict schema validation.
    DOES NOT execute tools directly.
    """

    def __init__(self, provider: Optional[OllamaProvider] = None, registry: Optional[ToolRegistry] = None):
        self.provider = provider or OllamaProvider()
        self.registry = registry or default_registry
        self.deterministic_router = IntentRouter()

    def _clean_and_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Safely extracts and parses JSON from raw LLM output without eval()."""
        if not raw_text or not raw_text.strip():
            return None

        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def _validate_and_build_request(self, data: Dict[str, Any], user_input: str, source: InputSource) -> RoutingResult:
        """Validates intent and parameters against ToolRegistry schemas."""
        intent = data.get("intent")
        params = data.get("parameters", {})

        if not intent or intent == "unknown":
            return RoutingResult(success=False, error="UNSUPPORTED: Query outside supported system tools.")

        # Tool Registry Existence Check
        if not self.registry.exists(intent):
            return RoutingResult(success=False, error=f"REJECTED: Tool '{intent}' is not registered.")

        # Parameter Validation
        if intent == "open_application":
            app_name = params.get("app_name")
            if not app_name or not isinstance(app_name, str):
                return RoutingResult(success=False, error="INVALID_PARAMS: app_name must be a non-empty string.")

        elif intent == "set_volume":
            level = params.get("level")
            if not isinstance(level, (int, float)) or not (0 <= int(level) <= 100):
                return RoutingResult(success=False, error="INVALID_PARAMS: level must be an integer between 0 and 100.")
            params["level"] = int(level)

        elif intent == "mute_audio":
            mute = params.get("mute")
            if not isinstance(mute, bool):
                return RoutingResult(success=False, error="INVALID_PARAMS: mute must be a boolean.")

        elif intent == "create_reminder":
            text = params.get("user_text", user_input)
            params["user_text"] = text

        return RoutingResult(
            success=True,
            task_request=TaskRequest(
                intent=intent,
                parameters=params,
                source=source,
                confidence=0.85,
                original_input=user_input,
            ),
        )

    def route(self, user_input: str, source: InputSource = InputSource.TEXT) -> RoutingResult:
        """
        Routing Cascade:
        1. Try Deterministic Router first (Zero LLM cost/latency)
        2. Fall back to LLMIntentRouter (qwen2.5:3b structured JSON generation)
        3. Reject invalid/conversational queries cleanly
        """
        # 1. Deterministic Pass
        det_result = self.deterministic_router.route(user_input, source=source)
        if det_result.success:
            return det_result

        # 2. LLM-Assisted Pass
        prompt = f"User Request: \"{user_input}\"\nReturn JSON:"
        raw_llm_response = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_ROUTER_PROMPT)

        if not raw_llm_response or raw_llm_response.startswith("[!]"):
            return RoutingResult(success=False, error=f"LLM_ROUTER_UNAVAILABLE: {raw_llm_response}")

        parsed_json = self._clean_and_parse_json(raw_llm_response)
        if not parsed_json or not isinstance(parsed_json, dict):
            return RoutingResult(success=False, error="PARSING_FAILED: Model returned malformed non-JSON output.")

        # 3. Validation & Building
        return self._validate_and_build_request(parsed_json, user_input, source)