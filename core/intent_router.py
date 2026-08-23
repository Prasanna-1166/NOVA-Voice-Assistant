import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class InputSource(Enum):
    TEXT = "TEXT"
    VOICE = "VOICE"


@dataclass
class TaskRequest:
    intent: str
    parameters: Dict[str, Any]
    source: InputSource = InputSource.TEXT
    confidence: float = 1.0
    original_input: str = ""


@dataclass
class RoutingResult:
    success: bool
    task_request: Optional[TaskRequest] = None
    error: Optional[str] = None


class IntentRouter:
    """
    Deterministic intent router for Phase 3.
    Parses natural-language commands into structured TaskRequests.
    Does NOT execute tools or make LLM calls directly.
    """

    def route(self, user_input: str, source: InputSource = InputSource.TEXT) -> RoutingResult:
        clean_input = user_input.strip()
        if not clean_input:
            return RoutingResult(success=False, error="Empty user input.")

        lowered = clean_input.lower()

        # 1. Open Application
        app_match = re.search(r"^open\s+([a-zA-Z0-9\s]+)", lowered)
        if app_match and not any(k in lowered for k in ["word", "document", "file"]):
            app_name = app_match.group(1).strip()
            if app_name:
                return RoutingResult(
                    success=True,
                    task_request=TaskRequest(
                        intent="open_application",
                        parameters={"app_name": app_name},
                        source=source,
                        original_input=user_input,
                    ),
                )

        # 2. Set Volume
        vol_match = re.search(r"(?:set|change)\s+volume\s+(?:to\s+)?(\d+)", lowered)
        if vol_match:
            try:
                level = int(vol_match.group(1))
                if 0 <= level <= 100:
                    return RoutingResult(
                        success=True,
                        task_request=TaskRequest(
                            intent="set_volume",
                            parameters={"level": level},
                            source=source,
                            original_input=user_input,
                        ),
                    )
                else:
                    return RoutingResult(success=False, error="Volume level out of bounds (0-100).")
            except ValueError:
                return RoutingResult(success=False, error="Invalid volume parameter.")

        # 3. Mute / Unmute
        if "unmute" in lowered:
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="mute_audio",
                    parameters={"mute": False},
                    source=source,
                    original_input=user_input,
                ),
            )
        elif "mute" in lowered:
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="mute_audio",
                    parameters={"mute": True},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 4. Take Screenshot
        if "screenshot" in lowered or "screen shot" in lowered:
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="take_screenshot",
                    parameters={},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 5. Create Reminder
        timer_match = re.search(r"remind\s+me\s+in\s+(\d+)\s*(sec|second|min|minute|hr|hour)s?\s*(?:to\s+)?(.+)", lowered)
        if timer_match:
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="create_reminder",
                    parameters={"user_text": user_input},
                    source=source,
                    original_input=user_input,
                ),
            )

        return RoutingResult(success=False, error="UNSUPPORTED: Intent could not be routed deterministically.")