import json
import re
from typing import Dict, Any, Optional
from core.intent_router import TaskRequest, InputSource, RoutingResult, IntentRouter
from core.llm import OllamaProvider
from core.tool_registry import ToolRegistry, default_registry


SYSTEM_ROUTER_PROMPT = """You are NOVA's intent classification engine.
Your sole responsibility is to analyze user input and map it to a supported capability intent.

Supported Capabilities & Intents:
System Productivity Tools:
1. "open_application" -> parameters: {"app_name": "<string>"}
2. "set_volume" -> parameters: {"level": <integer 0-100>}
3. "mute_audio" -> parameters: {"mute": <boolean>}
4. "take_screenshot" -> parameters: {}
5. "create_reminder" -> parameters: {"user_text": "<string>"}

Task & To-Do Management:
6. "create_task" -> parameters: {"title": "<string>", "priority": "<LOW|MEDIUM|HIGH>"}
7. "list_tasks" -> parameters: {"status": "<PENDING|COMPLETED>"}
8. "complete_task" -> parameters: {"task_identifier": "<string>"}
9. "update_task" -> parameters: {"task_identifier": "<string>", "title": "<string>", "priority": "<LOW|MEDIUM|HIGH>", "status": "<PENDING|COMPLETED>"}
10. "delete_task" -> parameters: {"task_identifier": "<string>"}

User Preferences:
11. "set_preference" -> parameters: {"key": "<string>", "value": "<string|number|boolean>"}
12. "get_preference" -> parameters: {"key": "<string>"}

Software Engineering & Coding Tasks:
13. "code_generation" -> parameters: {"query": "<string>"}
14. "code_explanation" -> parameters: {"query": "<string>"}
15. "debugging" -> parameters: {"query": "<string>"}
16. "algorithm_help" -> parameters: {"query": "<string>"}
17. "code_conversion" -> parameters: {"query": "<string>"}
18. "programming_guidance" -> parameters: {"query": "<string>"}

Document Generation Capabilities:
19. "report_generation" -> parameters: {"topic": "<string>"}
20. "assignment_generation" -> parameters: {"topic": "<string>"}
21. "note_generation" -> parameters: {"topic": "<string>"}
22. "project_documentation" -> parameters: {"topic": "<string>"}
23. "letter_generation" -> parameters: {"topic": "<string>"}
24. "resume_generation" -> parameters: {"topic": "<string>"}
25. "quiz_generation" -> parameters: {"topic": "<string>"}
26. "readme_generation" -> parameters: {"topic": "<string>"}
27. "document_generation" -> parameters: {"topic": "<string>"}

Rules:
- Respond strictly with a single valid JSON object.
- Never output Markdown code blocks, explanations, or text outside the JSON object.
- If the request is a general non-technical/conversational question, return: {"intent": "unknown", "parameters": {}}

Example Output:
{"intent": "create_task", "parameters": {"title": "DSA assignment", "priority": "HIGH"}}
"""


class LLMIntentRouter:

    def __init__(self, provider: Optional[OllamaProvider] = None, registry: Optional[ToolRegistry] = None):
        self.provider = provider or OllamaProvider()
        self.registry = registry or default_registry
        self.deterministic_router = IntentRouter()

    def _clean_and_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
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
        intent = data.get("intent")
        params = data.get("parameters", {})

        if not intent or intent == "unknown":
            return RoutingResult(success=False, error="UNSUPPORTED: Query outside supported intents.")

        non_tool_intents = [
            "code_generation", "code_explanation", "debugging", "algorithm_help",
            "code_conversion", "programming_guidance", "document_generation",
            "report_generation", "assignment_generation", "note_generation",
            "project_documentation", "letter_generation", "resume_generation",
            "quiz_generation", "readme_generation"
        ]

        if intent not in non_tool_intents and not self.registry.exists(intent):
            return RoutingResult(success=False, error=f"REJECTED: Intent '{intent}' is not supported.")

        # Parameter Validations & Normalizations
        if intent == "open_application":
            app_name = params.get("app_name")
            if not app_name or not isinstance(app_name, str):
                return RoutingResult(success=False, error="INVALID_PARAMS: app_name must be string.")

        elif intent == "set_volume":
            level = params.get("level")
            if not isinstance(level, (int, float)) or not (0 <= int(level) <= 100):
                return RoutingResult(success=False, error="INVALID_PARAMS: level must be 0-100.")
            params["level"] = int(level)

        elif intent == "mute_audio":
            if not isinstance(params.get("mute"), bool):
                return RoutingResult(success=False, error="INVALID_PARAMS: mute must be boolean.")

        elif intent == "create_task":
            title = params.get("title")
            if not title or not isinstance(title, str) or not title.strip():
                return RoutingResult(success=False, error="INVALID_PARAMS: title must be non-empty string.")

        elif intent in ["complete_task", "delete_task"]:
            ident = params.get("task_identifier")
            if not ident or not isinstance(ident, str) or not ident.strip():
                return RoutingResult(success=False, error="INVALID_PARAMS: task_identifier must be non-empty string.")

        elif intent == "set_preference":
            # Extract key/value flexibly from LLM outputs
            key = params.get("key") or params.get("preference_key") or params.get("preference")
            val = params.get("value") or params.get("preference_value") or params.get("val")
            if not key or val is None:
                return RoutingResult(success=False, error="INVALID_PARAMS: key and value are required for set_preference.")
            params = {"key": str(key).strip(), "value": str(val).strip()}

        elif intent == "get_preference":
            key = params.get("key") or params.get("preference_key") or params.get("preference")
            if not key or not isinstance(key, str) or not key.strip():
                return RoutingResult(success=False, error="INVALID_PARAMS: key must be non-empty string.")
            params = {"key": key.strip()}

        elif intent in non_tool_intents:
            if "topic" in params:
                params["topic"] = params.get("topic") or user_input
            elif "query" in params:
                params["query"] = params.get("query") or user_input
            else:
                params["topic"] = user_input

        return RoutingResult(
            success=True,
            task_request=TaskRequest(
                intent=intent,
                parameters=params,
                source=source,
                confidence=0.90,
                original_input=user_input,
            ),
        )

    def route(self, user_input: str, source: InputSource = InputSource.TEXT) -> RoutingResult:
        det_result = self.deterministic_router.route(user_input, source=source)
        if det_result.success:
            return det_result

        prompt = f"User Request: \"{user_input}\"\nReturn JSON:"
        raw_llm_response = self.provider.generate(prompt=prompt, system_prompt=SYSTEM_ROUTER_PROMPT)

        if not raw_llm_response or raw_llm_response.startswith("[!]"):
            return RoutingResult(success=False, error=f"LLM_ROUTER_UNAVAILABLE: {raw_llm_response}")

        parsed_json = self._clean_and_parse_json(raw_llm_response)
        if not parsed_json or not isinstance(parsed_json, dict):
            return RoutingResult(success=False, error="PARSING_FAILED: Malformed response.")

        return self._validate_and_build_request(parsed_json, user_input, source)