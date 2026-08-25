from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from rag.document_models import RetrievedChunk


class ContextType(Enum):
    CONVERSATION = "CONVERSATION"
    RAG = "RAG"
    TASKS = "TASKS"
    PREFERENCES = "PREFERENCES"
    REMINDERS = "REMINDERS"


@dataclass
class ContextRequest:
    query: str
    session_id: str = "default_session"
    intent: Optional[str] = None
    required_context_types: List[ContextType] = field(default_factory=list)
    max_memory_turns: int = 5
    max_rag_chunks: int = 3
    include_tasks: bool = False
    include_preferences: bool = False
    include_reminders: bool = False
    include_conversation: bool = True


@dataclass
class ContextBundle:
    query: str
    session_id: str = "default_session"
    conversation_context: List[Dict[str, str]] = field(default_factory=list)
    retrieved_documents: List[RetrievedChunk] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    reminders: List[Dict[str, Any]] = field(default_factory=list)

    def has_rag_context(self) -> bool:
        return len(self.retrieved_documents) > 0

    def format_rag_context(self) -> str:
        if not self.retrieved_documents:
            return ""
        blocks = []
        for item in self.retrieved_documents:
            c = item.chunk
            page_str = f" — Page {c.page_number}" if c.page_number else ""
            source_tag = f"{c.source_filename}{page_str}"
            blocks.append(f"[Source: {source_tag}]\n{c.text}")
        return "\n\n".join(blocks)