import json
from typing import Dict, Any, List

class Planner:
    """
    Generates structured multi-step plans and validates actions before execution.
    """

    SAFE_ACTIONS = {"read", "summarize", "retrieve", "list", "query"}
    RISKY_ACTIONS = {"delete", "execute_command", "update_system"}

    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry

    def create_plan(self, user_request: str) -> Dict[str, Any]:
        """Generates a structured plan schema from a user request."""
        lower_req = user_request.lower()
        steps = []

        if "summarize" in lower_req or "document" in lower_req:
            steps.append({
                "step_id": 1,
                "agent": "document",
                "action": "summarize",
                "requires_approval": False
            })

        if "task" in lower_req or "remind" in lower_req:
            steps.append({
                "step_id": len(steps) + 1,
                "agent": "productivity",
                "action": "create_task",
                "requires_approval": False
            })

        if not steps:
            steps.append({
                "step_id": 1,
                "agent": "general",
                "action": "respond",
                "requires_approval": False
            })

        return {
            "goal": user_request,
            "steps": steps
        }

    def validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validates steps for safety and authorization constraints."""
        for step in plan.get("steps", []):
            action = step.get("action", "")
            if action in self.RISKY_ACTIONS:
                step["requires_approval"] = True
                step["status"] = "PENDING_APPROVAL"
            else:
                step["status"] = "APPROVED"

        plan["is_valid"] = True
        return plan