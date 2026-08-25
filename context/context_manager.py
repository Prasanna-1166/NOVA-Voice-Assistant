from typing import Optional, Any
from context.context_models import ContextRequest, ContextBundle, ContextType
from memory.conversation_memory import ConversationMemory
from productivity.task_store import default_task_store, TaskStore
from productivity.preference_store import default_preference_store, PreferenceStore
from scheduling.reminder_store import default_reminder_store, ReminderStore


class ContextManager:
    """
    Central assembly layer aggregating ContextBundle from all local stores without executing actions.
    """

    def __init__(
        self,
        memory: Optional[ConversationMemory] = None,
        task_store: Optional[TaskStore] = None,
        pref_store: Optional[PreferenceStore] = None,
        reminder_store: Optional[ReminderStore] = None,
        rag_pipeline: Optional[Any] = None,
    ):
        self.memory = memory or ConversationMemory()
        self.task_store = task_store or default_task_store
        self.pref_store = pref_store or default_preference_store
        self.reminder_store = reminder_store or default_reminder_store

        if rag_pipeline is None:
            try:
                from rag.rag_pipeline import default_rag_pipeline
                self.rag_pipeline = default_rag_pipeline
            except Exception:
                self.rag_pipeline = None
        else:
            self.rag_pipeline = rag_pipeline

    def build_context(self, request: ContextRequest) -> ContextBundle:
        bundle = ContextBundle(query=request.query, session_id=request.session_id)

        # 1. Read Conversation Memory
        if request.include_conversation or ContextType.CONVERSATION in request.required_context_types:
            mem_history = []
            
            # Exhaustive check across all common Memory API patterns
            for method_name in ["get_context", "get_history", "get_messages", "load_session"]:
                if hasattr(self.memory, method_name):
                    try:
                        mem_history = getattr(self.memory, method_name)(session_id=request.session_id)
                    except TypeError:
                        try:
                            mem_history = getattr(self.memory, method_name)(request.session_id)
                        except TypeError:
                            pass
                if mem_history:
                    break

            # Fallback to direct attribute lookup if methods didn't return anything
            if not mem_history:
                if hasattr(self.memory, "messages") and isinstance(self.memory.messages, list):
                    mem_history = self.memory.messages
                elif hasattr(self.memory, "sessions") and isinstance(self.memory.sessions, dict):
                    session_data = self.memory.sessions.get(request.session_id)
                    if session_data:
                        mem_history = getattr(session_data, "messages", session_data)
                elif hasattr(self.memory, "_store") and isinstance(self.memory._store, dict):
                    mem_history = self.memory._store.get(request.session_id, [])

            max_msgs = request.max_memory_turns * 2
            if len(mem_history) > max_msgs:
                mem_history = mem_history[-max_msgs:]

            formatted_mem = []
            for item in mem_history:
                if isinstance(item, dict):
                    formatted_mem.append({
                        "role": item.get("role", item.get("sender", "user")),
                        "content": item.get("content", item.get("text", ""))
                    })
                else:
                    role = getattr(item, "role", getattr(item, "sender", "user"))
                    content = getattr(item, "content", getattr(item, "text", str(item)))
                    formatted_mem.append({"role": role, "content": content})

            bundle.conversation_context = formatted_mem

        # 2. Query RAG Vector Store
        if ContextType.RAG in request.required_context_types and self.rag_pipeline is not None:
            try:
                chunks = self.rag_pipeline.retriever.retrieve(
                    question=request.query,
                    top_k=request.max_rag_chunks,
                )
                bundle.retrieved_documents = chunks
            except Exception:
                bundle.retrieved_documents = []

        # 3. Read Task Store
        if request.include_tasks or ContextType.TASKS in request.required_context_types:
            tasks = self.task_store.list_tasks(status="PENDING")
            bundle.tasks = [{"id": t.id, "title": t.title, "priority": t.priority.value} for t in tasks]

        # 4. Read Preference Store
        if request.include_preferences or ContextType.PREFERENCES in request.required_context_types:
            bundle.preferences = self.pref_store.list_preferences()

        # 5. Read Reminder Store
        if request.include_reminders or ContextType.REMINDERS in request.required_context_types:
            rems = self.reminder_store.list_reminders(status="PENDING")
            bundle.reminders = [{"id": r.id, "title": r.title, "scheduled_time": r.scheduled_time} for r in rems]

        return bundle