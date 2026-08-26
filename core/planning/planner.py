import json
import re
import uuid
from typing import Optional, Dict, Any, List
from core.llm import OllamaProvider
from core.planning.plan_models import ExecutionPlan, PlanStep, PlanStatus
from core.planning.plan_validator import PlanValidator

PLANNER_SYSTEM_PROMPT = """You are NOVA's Multi-Step Planning Engine.
Your task is to decompose complex user requests into a structured DAG execution plan.

Supported Intents:
- Productivity: "create_task", "list_tasks", "complete_task", "delete_task", "create_reminder", "list_reminders", "cancel_reminder", "set_preference", "get_preference", "open_application", "set_volume", "mute_audio", "take_screenshot"
- Coding: "code_generation", "code_explanation", "debugging", "algorithm_help", "code_conversion", "programming_guidance"
- Document: "document_generation", "report_generation", "assignment_generation", "note_generation", "project_documentation", "letter_generation", "resume_generation", "quiz_generation", "readme_generation"
- RAG: "ingest_document", "query_documents", "list_knowledge_documents", "remove_document"

Output Format:
Return ONLY a raw JSON object with this exact key structure:
{
  "steps": [
    {
      "step_id": 1,
      "intent": "create_task",
      "parameters": {"title": "Study DSA"},
      "dependencies": []
    },
    {
      "step_id": 2,
      "intent": "create_reminder",
      "parameters": {"title": "Study DSA", "user_text": "remind me tomorrow at 7pm"},
      "dependencies": [1]
    }
  ]
}

Rules:
1. Every step must have a unique numeric 'step_id' starting at 1.
2. 'dependencies' must be a list of step_ids that MUST finish before this step executes.
3. Output strictly JSON. Do not include markdown or conversational commentary.
"""


class AgenticPlanner:
    """
    Decomposes user inputs into structured ExecutionPlans using deterministic logic
    or Ollama LLM fallback. Performs validation prior to returning.
    """

    def __init__(self, provider: Optional[OllamaProvider] = None):
        self.provider = provider or OllamaProvider()

    def is_multi_step_request(self, user_input: str) -> bool:
        lowered = user_input.lower().strip()

        # Fast exclusion for conversational questions or status checks
        conversational_starters = [
            "what is", "what are", "who is", "tell me", "explain",
            "capabilities", "abilities", "how do I", "show my", "list my", "hi", "hello"
        ]
        if any(lowered.startswith(phrase) or phrase in lowered for phrase in ["capabilities", "abilities"]):
            return False

        connectives = [" and ", " also ", " then ", " after that ", " as well as "]
        count = sum(1 for c in connectives if c in lowered)
        if count >= 1 or lowered.count(",") >= 2:
            return True
        return False

    def create_plan(self, user_input: str) -> ExecutionPlan:
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        # 1. Deterministic Multi-Step Splitter heuristic
        deterministic_plan = self._try_deterministic_plan(plan_id, user_input)
        if deterministic_plan:
            valid, msg = PlanValidator.validate(deterministic_plan)
            if valid:
                return deterministic_plan

        # 2. LLM Multi-Step Plan Generation Fallback
        prompt = f"User Request: \"{user_input}\"\nGenerate Plan JSON:"
        raw_resp = self.provider.generate(prompt=prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
        
        plan = self._parse_llm_response(plan_id, user_input, raw_resp)
        valid, msg = PlanValidator.validate(plan)
        if not valid:
            plan.status = PlanStatus.FAILED
            plan.error = msg
        return plan

    def _try_deterministic_plan(self, plan_id: str, user_input: str) -> Optional[ExecutionPlan]:
        lowered = user_input.lower()
        
        # Example: "create task to study DSA and remind me to study DSA"
        if "create task" in lowered and ("remind" in lowered or "reminder" in lowered):
            task_title = "Study DSA"
            task_match = re.search(r"task\s+(?:to\s+)?([^and,]+)", user_input, re.IGNORECASE)
            if task_match:
                task_title = task_match.group(1).strip()

            step1 = PlanStep(step_id=1, intent="create_task", parameters={"title": task_title})
            step2 = PlanStep(
                step_id=2,
                intent="create_reminder",
                parameters={"title": task_title, "user_text": user_input},
                dependencies=[1]
            )
            return ExecutionPlan(plan_id=plan_id, user_request=user_input, steps=[step1, step2])
            
        return None

    def _parse_llm_response(self, plan_id: str, user_input: str, raw_text: str) -> ExecutionPlan:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if not match:
                return ExecutionPlan(plan_id=plan_id, user_request=user_input, status=PlanStatus.FAILED, error="PARSING_ERROR: No valid JSON block returned.")
            
            data = json.loads(match.group(1))
            raw_steps = data.get("steps", [])
            steps: List[PlanStep] = []

            for item in raw_steps:
                steps.append(
                    PlanStep(
                        step_id=int(item.get("step_id")),
                        intent=str(item.get("intent")),
                        parameters=dict(item.get("parameters", {})),
                        dependencies=[int(d) for d in item.get("dependencies", [])],
                    )
                )

            return ExecutionPlan(plan_id=plan_id, user_request=user_input, steps=steps)
        except Exception as e:
            return ExecutionPlan(
                plan_id=plan_id,
                user_request=user_input,
                status=PlanStatus.FAILED,
                error=f"PARSING_ERROR: Failed to parse plan structure ({e})"
            )