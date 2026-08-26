from typing import Optional, Any

from context.context_models import (
    ContextRequest,
    ContextBundle,
    ContextType,
)

from memory.conversation_memory import ConversationMemory

from productivity.task_store import (
    default_task_store,
    TaskStore,
)

from productivity.preference_store import (
    default_preference_store,
    PreferenceStore,
)

from scheduling.reminder_store import (
    default_reminder_store,
    ReminderStore,
)


class ContextManager:
    """
    Central assembly layer responsible for aggregating
    context from all local stores.

    The ContextManager only reads and assembles context.
    It does not execute tools or perform actions.
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

        self.pref_store = (
            pref_store or default_preference_store
        )

        self.reminder_store = (
            reminder_store or default_reminder_store
        )

        # Initialize RAG pipeline if available.
        if rag_pipeline is None:
            try:
                from rag.rag_pipeline import default_rag_pipeline

                self.rag_pipeline = default_rag_pipeline

            except Exception:
                self.rag_pipeline = None

        else:
            self.rag_pipeline = rag_pipeline

    def build_context(
        self,
        request: ContextRequest
    ) -> ContextBundle:
        """
        Build a ContextBundle for the current request.

        Context can be assembled from:
        - Conversation memory
        - RAG documents
        - Tasks
        - Preferences
        - Reminders

        No actions are executed here.
        """

        bundle = ContextBundle(
            query=request.query,
            session_id=request.session_id,
        )

        # ==========================================================
        # 1. Conversation Memory
        # ==========================================================

        if (
            request.include_conversation
            or ContextType.CONVERSATION
            in request.required_context_types
        ):
            try:
                # ConversationMemory exposes get_recent_messages()
                # as its canonical retrieval API.
                mem_history = self.memory.get_recent_messages(
                    session_id=request.session_id,
                    limit=request.max_memory_turns * 2,
                )

            except TypeError:
                # Compatibility fallback for alternative
                # implementations/signatures.
                mem_history = self.memory.get_recent_messages(
                    request.session_id,
                    request.max_memory_turns * 2,
                )

            # Ensure the bundle always contains a list.
            if mem_history is None:
                mem_history = []

            formatted_mem = []

            for item in mem_history:

                # Handle dictionary-based messages.
                if isinstance(item, dict):
                    formatted_mem.append(
                        {
                            "role": item.get(
                                "role",
                                item.get("sender", "user"),
                            ),
                            "content": item.get(
                                "content",
                                item.get("text", ""),
                            ),
                        }
                    )

                # Handle Message dataclass/object.
                else:
                    formatted_mem.append(
                        {
                            "role": getattr(
                                item,
                                "role",
                                getattr(
                                    item,
                                    "sender",
                                    "user",
                                ),
                            ),
                            "content": getattr(
                                item,
                                "content",
                                getattr(
                                    item,
                                    "text",
                                    str(item),
                                ),
                            ),
                        }
                    )

            bundle.conversation_context = formatted_mem

        # ==========================================================
        # 2. RAG Vector Store
        # ==========================================================

        if (
            ContextType.RAG
            in request.required_context_types
            and self.rag_pipeline is not None
        ):
            try:
                chunks = self.rag_pipeline.retriever.retrieve(
                    question=request.query,
                    top_k=request.max_rag_chunks,
                )

                bundle.retrieved_documents = chunks

            except Exception:
                # RAG failure should not break unrelated
                # context sources.
                bundle.retrieved_documents = []

        # ==========================================================
        # 3. Task Store
        # ==========================================================

        if (
            request.include_tasks
            or ContextType.TASKS
            in request.required_context_types
        ):
            tasks = self.task_store.list_tasks(
                status="PENDING"
            )

            bundle.tasks = [
                {
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.value,
                }
                for task in tasks
            ]

        # ==========================================================
        # 4. Preference Store
        # ==========================================================

        if (
            request.include_preferences
            or ContextType.PREFERENCES
            in request.required_context_types
        ):
            bundle.preferences = (
                self.pref_store.list_preferences()
            )

        # ==========================================================
        # 5. Reminder Store
        # ==========================================================

        if (
            request.include_reminders
            or ContextType.REMINDERS
            in request.required_context_types
        ):
            reminders = self.reminder_store.list_reminders(
                status="PENDING"
            )

            bundle.reminders = [
                {
                    "id": reminder.id,
                    "title": reminder.title,
                    "scheduled_time": reminder.scheduled_time,
                }
                for reminder in reminders
            ]

        return bundle