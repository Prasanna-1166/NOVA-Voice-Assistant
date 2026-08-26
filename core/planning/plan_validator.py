from graphlib import TopologicalSorter, CycleError
from typing import Dict, Any, Tuple
from core.planning.plan_models import ExecutionPlan


class PlanValidator:
    """
    Validates execution plans for structural integrity, valid step references,
    cycle-free DAG dependencies, and authorized capabilities.
    """

    SUPPORTED_INTENTS = {
        "open_application", "set_volume", "mute_audio", "take_screenshot",
        "create_reminder", "list_reminders", "cancel_reminder",
        "create_task", "list_tasks", "complete_task", "update_task", "delete_task",
        "set_preference", "get_preference",
        "code_generation", "code_explanation", "debugging", "algorithm_help",
        "code_conversion", "programming_guidance",
        "document_generation", "report_generation", "assignment_generation",
        "note_generation", "project_documentation", "letter_generation",
        "resume_generation", "quiz_generation", "readme_generation",
        "ingest_document", "query_documents", "list_knowledge_documents", "remove_document"
    }

    @classmethod
    def validate(cls, plan: ExecutionPlan) -> Tuple[bool, str]:
        if not plan.steps:
            return False, "VALIDATION_ERROR: Plan contains no execution steps."

        step_ids = {s.step_id for s in plan.steps}
        if len(step_ids) != len(plan.steps):
            return False, "VALIDATION_ERROR: Duplicate step IDs detected in plan."

        # Build DAG graph for cycle detection (graphlib expects child -> set(predecessors))
        dag_graph: Dict[int, set] = {}

        for step in plan.steps:
            if step.intent not in cls.SUPPORTED_INTENTS:
                return False, f"VALIDATION_ERROR: Unsupported step intent '{step.intent}' at step {step.step_id}."

            for dep in step.dependencies:
                if dep == step.step_id:
                    return False, f"VALIDATION_ERROR: Step {step.step_id} cannot depend on itself."
                if dep not in step_ids:
                    return False, f"VALIDATION_ERROR: Step {step.step_id} references non-existent dependency {dep}."

            dag_graph[step.step_id] = set(step.dependencies)

        # Detect cyclic dependencies using graphlib.TopologicalSorter
        try:
            sorter = TopologicalSorter(dag_graph)
            sorter.prepare()
        except CycleError as e:
            return False, f"VALIDATION_ERROR: Circular dependency detected in plan: {e}"
        except Exception as e:
            return False, f"VALIDATION_ERROR: Invalid plan dependency graph: {e}"

        return True, "VALIDATION_SUCCESS"