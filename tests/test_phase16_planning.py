import unittest
from core.planning.plan_models import ExecutionPlan, PlanStep, PlanStatus, StepStatus
from core.planning.plan_validator import PlanValidator
from core.planning.planner import AgenticPlanner
from core.planning.plan_executor import PlanExecutor
from core.manager_agent import ManagerAgent


class TestPhase16Planning(unittest.TestCase):

    def test_plan_validator_success(self):
        plan = ExecutionPlan(
            plan_id="p1",
            user_request="test",
            steps=[
                PlanStep(step_id=1, intent="create_task", parameters={"title": "T1"}),
                PlanStep(step_id=2, intent="create_reminder", parameters={"title": "R1"}, dependencies=[1]),
            ]
        )
        valid, msg = PlanValidator.validate(plan)
        self.assertTrue(valid)
        self.assertEqual(msg, "VALIDATION_SUCCESS")

    def test_plan_validator_cycle_rejection(self):
        plan = ExecutionPlan(
            plan_id="p_cycle",
            user_request="test cycle",
            steps=[
                PlanStep(step_id=1, intent="create_task", parameters={"title": "T1"}, dependencies=[2]),
                PlanStep(step_id=2, intent="create_reminder", parameters={"title": "R1"}, dependencies=[1]),
            ]
        )
        valid, msg = PlanValidator.validate(plan)
        self.assertFalse(valid)
        self.assertIn("Circular dependency", msg)

    def test_deterministic_planner_multi_step(self):
        planner = AgenticPlanner()
        plan = planner.create_plan("create task to study DSA and remind me to study DSA")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].intent, "create_task")
        self.assertEqual(plan.steps[1].intent, "create_reminder")
        self.assertEqual(plan.steps[1].dependencies, [1])

    def test_executor_skips_failed_dependencies(self):
        # Setup mock manager that fails step 1
        class MockFailingManager(ManagerAgent):
            def process_task(self, task_request, session_id="default_session"):
                from core.agent import AgentResult
                if task_request.intent == "create_task":
                    return AgentResult(success=False, output=None, agent_name="Mock", error="Task Store full")
                return AgentResult(success=True, output="Success", agent_name="Mock")

        executor = PlanExecutor(manager_agent=MockFailingManager())
        plan = ExecutionPlan(
            plan_id="p_fail",
            user_request="test fail",
            steps=[
                PlanStep(step_id=1, intent="create_task", parameters={"title": "T1"}),
                PlanStep(step_id=2, intent="create_reminder", parameters={"title": "R1"}, dependencies=[1]),
            ]
        )
        executed = executor.execute_plan(plan)
        self.assertEqual(executed.status, PlanStatus.FAILED)
        self.assertEqual(executed.steps[0].status, StepStatus.FAILED)
        self.assertEqual(executed.steps[1].status, StepStatus.SKIPPED)


if __name__ == "__main__":
    unittest.main()