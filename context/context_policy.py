from typing import List, Dict, Any
import re
from context.context_models import ContextType, ContextRequest


class ContextPolicy:
    """
    Deterministic rules engine deciding which context stores must be queried.
    """

    @classmethod
    def evaluate(cls, intent: str, query: str, session_id: str = "default_session") -> ContextRequest:
        lowered = query.lower()
        req = ContextRequest(query=query, session_id=session_id, intent=intent)

        # Detect RAG references in query
        rag_triggered = bool(
            re.search(
                r"\b(notes|document|documents|pdf|textbook|file|files|uploaded|rag|deadlock|dsa)\b",
                lowered,
            )
        ) or intent in ["query_documents", "rag_query", "document_grounded_question", "document_based_code_explanation"]

        if intent in ["query_documents", "rag_query", "document_grounded_question"]:
            req.required_context_types = [ContextType.RAG, ContextType.CONVERSATION]
            req.include_conversation = True
            req.max_rag_chunks = 4

        elif intent == "generate_document":
            req.required_context_types = [ContextType.CONVERSATION]
            req.include_conversation = True
            if rag_triggered:
                req.required_context_types.append(ContextType.RAG)
                req.max_rag_chunks = 4

        elif intent in ["generate_code", "explain_code"]:
            req.required_context_types = [ContextType.CONVERSATION, ContextType.PREFERENCES]
            req.include_preferences = True
            req.include_conversation = True
            if rag_triggered:
                req.required_context_types.append(ContextType.RAG)

        elif intent in ["list_tasks", "complete_task", "delete_task", "create_task"]:
            req.required_context_types = [ContextType.TASKS, ContextType.CONVERSATION]
            req.include_tasks = True

        elif intent in ["list_reminders", "cancel_reminder", "create_reminder"]:
            req.required_context_types = [ContextType.REMINDERS, ContextType.CONVERSATION]
            req.include_reminders = True

        elif intent in ["get_preference", "set_preference"]:
            req.required_context_types = [ContextType.PREFERENCES]
            req.include_preferences = True

        else:
            # Default General Conversation
            req.required_context_types = [ContextType.CONVERSATION]
            req.include_conversation = True
            if rag_triggered:
                req.required_context_types.append(ContextType.RAG)

        return req