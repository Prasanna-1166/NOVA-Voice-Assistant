from typing import Optional, List
from core.agent import Agent, AgentResult
from core.intent_router import TaskRequest
from core.llm import OllamaProvider

CODING_SYSTEM_PROMPT = """You are NOVA's specialized Coding Agent, an expert software development assistant for engineering students.
Your task is to assist with programming, debugging, code explanation, algorithm analysis, and architecture guidance.

Rules:
1. Provide clear, correct, readable, and well-commented code.
2. Format all code strictly within Markdown code blocks (e.g., ```python ... ```).
3. Include brief explanations, complexity analysis (where relevant), and important notes.
4. If code or error context is missing from the user request, ask for the missing details politely.
5. NEVER claim that you executed code or system commands. You provide static analysis and code generation only.
"""


class CodingAgent(Agent):
    """
    Specialized NOVA Agent for software engineering, algorithm design,
    code explanation, and debugging assistance.
    """

    DEFAULT_ALLOWED_TOOLS: List[str] = []

    def __init__(
        self,
        name: str = "CodingAgent",
        description: str = "Specialized AI agent for programming, debugging, code explanation, algorithm assistance, and software development guidance.",
        provider: Optional[OllamaProvider] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            capabilities=[
                "code_generation",
                "code_explanation",
                "debugging",
                "algorithm_help",
                "code_conversion",
                "programming_guidance",
            ],
            allowed_tools=self.DEFAULT_ALLOWED_TOOLS,
        )
        self.provider = provider or OllamaProvider()

    def process_task(self, task_request: TaskRequest) -> AgentResult:
        """
        Processes a coding TaskRequest by generating structured code/explanation
        via OllamaProvider without executing raw system binaries.
        """
        prompt = task_request.original_input or task_request.parameters.get("query", "")
        if not prompt:
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error="EMPTY_QUERY: Coding task request contained no prompt or input text.",
            )

        llm_response = self.provider.generate(prompt=prompt, system_prompt=CODING_SYSTEM_PROMPT)

        if not llm_response or llm_response.startswith("[!]"):
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"LLM_GENERATION_FAILED: {llm_response}",
            )

        return AgentResult(
            success=True,
            output=llm_response,
            agent_name=self.name,
            error=None,
        )