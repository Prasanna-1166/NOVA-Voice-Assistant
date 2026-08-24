import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


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
    Deterministic intent router for NOVA V2.
    Parses natural-language commands into structured TaskRequests.
    Does NOT execute tools or make LLM calls directly.
    """

    def _parse_time(self, text: str) -> Optional[str]:
        """Parses relative time expressions into ISO datetime strings."""
        now = datetime.now()

        # Seconds, minutes, hours offset
        match = re.search(
            r"in\s+(\d+)\s*(sec|second|min|minute|hr|hour)s?",
            text
        )

        if match:
            amount = int(match.group(1))
            unit = match.group(2)

            if unit.startswith("sec"):
                delta = timedelta(seconds=amount)
            elif unit.startswith("min"):
                delta = timedelta(minutes=amount)
            else:
                delta = timedelta(hours=amount)

            return (now + delta).isoformat()

        return None

    def route(
        self,
        user_input: str,
        source: InputSource = InputSource.TEXT
    ) -> RoutingResult:

        clean_input = user_input.strip()

        if not clean_input:
            return RoutingResult(
                success=False,
                error="Empty user input."
            )

        lowered = clean_input.lower()

        # 1. Open Application
        app_match = re.search(
            r"^open\s+([a-zA-Z0-9\s]+)",
            lowered
        )

        if app_match and not any(
            k in lowered for k in ["word", "document", "file"]
        ):
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
        vol_match = re.search(
            r"(?:set|change)\s+volume\s+(?:to\s+)?(\d+)",
            lowered
        )

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

                return RoutingResult(
                    success=False,
                    error="Volume level out of bounds (0-100)."
                )

            except ValueError:
                return RoutingResult(
                    success=False,
                    error="Invalid volume parameter."
                )

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

        # 5. List Reminders
        if re.search(
            r"\b(show|list|get|view|display)\b.*\b(reminder|reminders)\b",
            lowered
        ):
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="list_reminders",
                    parameters={"status": "PENDING"},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 6. Cancel / Delete Reminder
        if re.search(
            r"\b(cancel|delete|remove)\b.*\b(reminder|reminders)\b",
            lowered
        ):
            match = re.search(
                r"\b(cancel|delete|remove)\b\s+"
                r"(?:my\s+)?(?:reminder\s+)?(.+)",
                lowered
            )

            target = match.group(2).strip() if match else lowered

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="cancel_reminder",
                    parameters={"identifier": target},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 7. Create Reminder
        if "remind" in lowered or "reminder" in lowered:
            time_iso = self._parse_time(lowered)

            title_match = re.search(
                r"\bto\s+(.+)$",
                user_input,
                re.IGNORECASE
            )

            title = (
                title_match.group(1).strip()
                if title_match
                else user_input
            )

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="create_reminder",
                    parameters={
                        "title": title,
                        "scheduled_time": time_iso,
                        "user_text": user_input,
                    },
                    source=source,
                    original_input=user_input,
                ),
            )

        # 8. Document Removal (Check BEFORE Task Deletion to avoid conflict)
        # Examples: "remove document os_notes.txt", "delete file os_notes.txt"
        remove_doc_match = re.search(
            r"\b(remove|delete)\b\s+(?:document|file|notes|pdf)\s+(.+)",
            lowered
        )
        if remove_doc_match:
            target_doc = remove_doc_match.group(2).strip()
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="remove_document",
                    parameters={"file_path": target_doc},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 9. Create Task
        if re.search(
            r"\b(create|add|new)\b.*\btask\b",
            lowered
        ):
            match = re.search(
                r"\b(?:create|add|new)\s+"
                r"(?:a\s+)?task\s+(?:to\s+)?(.+)",
                user_input,
                re.IGNORECASE
            )

            title = (
                match.group(1).strip()
                if match
                else user_input
            )

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="create_task",
                    parameters={"title": title},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 10. List Tasks
        if re.search(
            r"\b(show|list|get|view|display)\b.*\b(task|tasks)\b",
            lowered
        ):
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="list_tasks",
                    parameters={"status": "PENDING"},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 11. Complete Task
        if re.search(
            r"\b(complete|finish|done|mark)\b.*\btask\b",
            lowered
        ):
            match = re.search(
                r"\b(?:complete|finish|done|mark)\s+"
                r"(?:the\s+)?(?:task\s+)?(.+)",
                user_input,
                re.IGNORECASE
            )

            target = (
                match.group(1).strip()
                if match
                else user_input
            )

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="complete_task",
                    parameters={"task_identifier": target},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 12. Delete Task
        if re.search(
            r"\b(delete|remove)\b.*\btask\b",
            lowered
        ):
            match = re.search(
                r"\b(?:delete|remove)\s+"
                r"(?:the\s+)?(?:task\s+)?(.+)",
                user_input,
                re.IGNORECASE
            )

            target = (
                match.group(1).strip()
                if match
                else user_input
            )

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="delete_task",
                    parameters={"task_identifier": target},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 13. Set Preference
        if (
            "set my preferred" in lowered
            or "set preference" in lowered
        ):
            match = re.search(
                r"set\s+(?:my\s+preferred\s+|preference\s+)"
                r"([a-zA-Z0-9_\s]+)\s+to\s+(.+)",
                user_input,
                re.IGNORECASE
            )

            if match:
                key = match.group(1).strip().replace(" ", "_")
                val = match.group(2).strip()

                return RoutingResult(
                    success=True,
                    task_request=TaskRequest(
                        intent="set_preference",
                        parameters={
                            "key": key,
                            "value": val
                        },
                        source=source,
                        original_input=user_input,
                    ),
                )

        # 14. Get Preference
        if (
            "what is my preferred" in lowered
            or "get preference" in lowered
        ):
            match = re.search(
                r"(?:what\s+is\s+my\s+preferred|get\s+preference)\s+"
                r"([a-zA-Z0-9_\s\?]+)",
                user_input,
                re.IGNORECASE
            )

            if match:
                key = (
                    match.group(1)
                    .replace("?", "")
                    .strip()
                    .replace(" ", "_")
                )

                return RoutingResult(
                    success=True,
                    task_request=TaskRequest(
                        intent="get_preference",
                        parameters={"key": key},
                        source=source,
                        original_input=user_input,
                    ),
                )

        # 15. Document Ingestion
        ingest_match = re.search(
            r"\b(add|ingest|index|upload|import)\b.*"
            r"\b(document|file|pdf|notes)\b\s+(.+)",
            lowered
        )

        if ingest_match:
            path_str = ingest_match.group(3).strip()

            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="ingest_document",
                    parameters={"file_path": path_str},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 16. Document Querying (RAG Context Retrieval)
        if re.search(
            r"\b(according to my|in my notes|from my document|in my pdf|search my notes|what does my document say|what do my notes say|what does the document say)\b",
            lowered
        ):
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="query_documents",
                    parameters={"query": user_input},
                    source=source,
                    original_input=user_input,
                ),
            )

        # 17. List Indexed Knowledge Documents
        if re.search(
            r"\b(list|show)\b.*\b(indexed|knowledge|rag)\b.*"
            r"\b(documents|files|notes)\b",
            lowered
        ):
            return RoutingResult(
                success=True,
                task_request=TaskRequest(
                    intent="list_knowledge_documents",
                    parameters={},
                    source=source,
                    original_input=user_input,
                ),
            )

        return RoutingResult(
            success=False,
            error="UNSUPPORTED: Intent could not be routed deterministically."
        )