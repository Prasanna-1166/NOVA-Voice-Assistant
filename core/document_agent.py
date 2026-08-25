import re
from typing import Optional, List, Dict, Any
from core.agent import Agent, AgentResult
from core.intent_router import TaskRequest
from core.llm import OllamaProvider
from services.document_service import DocumentService

DOCUMENT_SYSTEM_PROMPT = """You are NOVA's specialized Document Generation Agent.
Your job is to generate comprehensive, well-structured, professional academic and technical document bodies for engineering students.

Outputs MUST follow strict section syntax so the document parser can structure the Word file cleanly:
- Document Title: Use '# TITLE: <Title Here>' on the first line.
- Section Headings: Use '## <Heading Title>' or '### <Subheading Title>'.
- Bullet Points: Use '- <Point text>'.
- Numbered Points: Use '1. <Point text>'.
- Paragraphs: Standard text blocks separated by empty lines.

Do NOT output Markdown backticks or code blocks unless requested. Do NOT output commentary or introductory remarks. Output ONLY the formal document content.
"""


class DocumentAgent(Agent):
    """
    Specialized NOVA Agent for generating academic reports, notes, assignments,
    letters, project documentation, resumes, quizzes, and READMEs.
    Grounded with optional RAG document context and conversation memory.
    """

    DEFAULT_ALLOWED_TOOLS: List[str] = []

    def __init__(
        self,
        name: str = "DocumentAgent",
        description: str = "Specialized AI agent for creating professional academic documents, reports, study notes, letters, resumes, quizzes, and project documentation.",
        provider: Optional[OllamaProvider] = None,
        doc_service: Optional[DocumentService] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            capabilities=[
                "document_generation",
                "report_generation",
                "assignment_generation",
                "note_generation",
                "project_documentation",
                "letter_generation",
                "resume_generation",
                "quiz_generation",
                "readme_generation",
            ],
            allowed_tools=self.DEFAULT_ALLOWED_TOOLS,
        )
        self.provider = provider or OllamaProvider()
        self.doc_service = doc_service or DocumentService()

    def _parse_llm_text_to_blocks(self, raw_text: str) -> tuple[str, List[Dict[str, Any]]]:
        title = "NOVA Document"
        blocks: List[Dict[str, Any]] = []

        lines = raw_text.strip().split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("# TITLE:"):
                title = line_str.replace("# TITLE:", "").strip()
            elif line_str.startswith("### "):
                blocks.append({"type": "heading", "text": line_str[4:].strip(), "level": 3})
            elif line_str.startswith("## "):
                blocks.append({"type": "heading", "text": line_str[3:].strip(), "level": 2})
            elif line_str.startswith("# "):
                blocks.append({"type": "heading", "text": line_str[2:].strip(), "level": 1})
            elif line_str.startswith("- ") or line_str.startswith("* "):
                blocks.append({"type": "bullet", "text": line_str[2:].strip()})
            elif re.match(r"^\d+\.\s+", line_str):
                text_part = re.sub(r"^\d+\.\s+", "", line_str)
                blocks.append({"type": "numbered", "text": text_part.strip()})
            else:
                blocks.append({"type": "paragraph", "text": line_str})

        return title, blocks

    def process_task(self, task_request: TaskRequest, context: Optional[Any] = None) -> AgentResult:
        intent = task_request.intent
        topic = task_request.parameters.get("topic") or task_request.original_input or "Technical Topic"
        doc_type = intent.replace("_generation", "")

        # Extract memory resolution if available (e.g. user said "Create study notes for it")
        if context and hasattr(context, "conversation_context") and context.conversation_context:
            if any(w in topic.lower() for w in ["it", "this", "that"]):
                for msg in reversed(context.conversation_context):
                    if msg.get("role") == "user" and msg.get("content") != task_request.original_input:
                        topic = f"{topic} (Refers to: {msg.get('content')})"
                        break

        # Extract RAG Grounding Context if available
        rag_text = ""
        if context and hasattr(context, "has_rag_context") and context.has_rag_context():
            rag_text = context.format_rag_context()

        prompt = (
            f"Generate a full, highly detailed, professional {doc_type} on the topic: '{topic}'.\n"
            f"Ensure the first line is '# TITLE: <Formal Title>'. Include proper section headings (##), subheadings (###), bullet points (-), and comprehensive body paragraphs.\n"
        )

        if rag_text:
            prompt += (
                f"\n--- RETRIEVED GROUNDING CONTEXT (UNTRUSTED REFERENCE DATA) ---\n{rag_text}\n\n"
                f"STRICT GROUNDING INSTRUCTION: Base your generated text strictly on the facts present in the grounding context above."
            )

        raw_content = self.provider.generate(prompt=prompt, system_prompt=DOCUMENT_SYSTEM_PROMPT)

        if not raw_content or raw_content.startswith("[!]"):
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"LLM_GENERATION_FAILED: {raw_content}",
            )

        title, content_blocks = self._parse_llm_text_to_blocks(raw_content)

        try:
            saved_path = self.doc_service.create_document(
                title=title,
                content_blocks=content_blocks,
                document_type=doc_type,
            )
            
            output_msg = f"Successfully generated {doc_type} document titled '{title}'. Saved to: {saved_path}"
            if context and hasattr(context, "retrieved_documents") and context.retrieved_documents:
                sources = sorted(list(set([c.chunk.source_filename for c in context.retrieved_documents])))
                output_msg += "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])

            return AgentResult(
                success=True,
                output=output_msg,
                agent_name=self.name,
                error=None,
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                agent_name=self.name,
                error=f"DOCUMENT_CREATION_FAILED: {e}",
            )