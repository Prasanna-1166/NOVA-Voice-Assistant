from graphlib import TopologicalSorter
from typing import Optional, Dict, Any
from core.planning.plan_models import ExecutionPlan, PlanStatus, StepStatus, PlanStep
from core.planning.plan_validator import PlanValidator
from core.manager_agent import ManagerAgent
from core.intent_router import TaskRequest, InputSource


class PlanExecutor:
    """
    Executes a validated ExecutionPlan step-by-step using ManagerAgent while respecting DAG dependencies.
    Performs partial failure management and skips steps blocked by broken prerequisites.
    """

    def __init__(self, manager_agent: Optional[ManagerAgent] = None):
        self.manager_agent = manager_agent or ManagerAgent()

    def execute_plan(self, plan: ExecutionPlan, session_id: str = "default_session") -> ExecutionPlan:
        valid, msg = PlanValidator.validate(plan)
        if not valid:
            plan.status = PlanStatus.FAILED
            plan.error = msg
            return plan

        plan.status = PlanStatus.RUNNING

        # Compute valid step order using TopologicalSorter
        dag_dict = {step.step_id: set(step.dependencies) for step in plan.steps}
        sorter = TopologicalSorter(dag_dict)
        execution_order = list(sorter.static_order())

        completed_count = 0
        failed_count = 0

        for step_id in execution_order:
            step = plan.get_step(step_id)
            if not step:
                continue

            # Check if all dependency steps succeeded
            deps_ok = True
            for dep_id in step.dependencies:
                dep_step = plan.get_step(dep_id)
                if not dep_step or dep_step.status != StepStatus.COMPLETED:
                    deps_ok = False
                    break

            if not deps_ok:
                step.status = StepStatus.SKIPPED
                step.error = "SKIPPED: Prerequisites failed or were skipped."
                continue

            # Execute Step via ManagerAgent / TaskRequest
            step.status = StepStatus.RUNNING
            task_req = TaskRequest(
                intent=step.intent,
                parameters=step.parameters,
                source=InputSource.TEXT,
                original_input=plan.user_request,
            )

            res = self.manager_agent.process_task(task_req, session_id=session_id)

            if res.success:
                step.status = StepStatus.COMPLETED
                step.result = res.output
                completed_count += 1
            else:
                step.status = StepStatus.FAILED
                step.error = res.error or "Step execution failed."
                failed_count += 1

        # Finalize Plan Status
        if completed_count == len(plan.steps):
            plan.status = PlanStatus.COMPLETED
        elif completed_count > 0:
            plan.status = PlanStatus.PARTIALLY_COMPLETED
        else:
            plan.status = PlanStatus.FAILED

        return plan

    def format_summary(self, plan: ExecutionPlan) -> str:
        lines = [f"**Execution Summary for Plan [{plan.plan_id}]** (Status: {plan.status.value}):\n"]

        for step in plan.steps:
            icon = "✅" if step.status == StepStatus.COMPLETED else ("❌" if step.status == StepStatus.FAILED else "⚠️")
            detail = f"{step.result}" if step.status == StepStatus.COMPLETED else f"{step.error}"
            lines.append(f"{icon} **Step {step.step_id}** [{step.intent}]: {detail}")

        return "\n".join(lines)