import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from core.document_agent import DocumentAgent
from core.intent_router import TaskRequest, InputSource


class TestDocumentAgent(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MagicMock()
        self.mock_service = MagicMock()
        self.agent = DocumentAgent(provider=self.mock_provider, doc_service=self.mock_service)

    def test_document_agent_metadata(self):
        self.assertEqual(self.agent.name, "DocumentAgent")
        self.assertIn("report_generation", self.agent.capabilities)
        self.assertIn("note_generation", self.agent.capabilities)
        self.assertEqual(self.agent.allowed_tools, [])

    def test_successful_report_generation(self):
        self.mock_provider.generate.return_value = (
            "# TITLE: AI in Healthcare Report\n## Introduction\nArtificial Intelligence is transforming medical technology.\n- Diagnostic accuracy\n- Robotic surgery"
        )
        self.mock_service.create_document.return_value = Path("C:/Users/User/Documents/NOVA/AI_in_Healthcare_Report.docx")

        task = TaskRequest(
            intent="report_generation",
            parameters={"topic": "Artificial Intelligence in Healthcare"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertTrue(res.success)
        self.assertEqual(res.agent_name, "DocumentAgent")
        self.assertIn("AI_in_Healthcare_Report.docx", res.output)
        self.mock_service.create_document.assert_called_once()

    def test_successful_notes_generation(self):
        self.mock_provider.generate.return_value = (
            "# TITLE: OS Deadlocks Notes\n## Key Concepts\nDeadlock occurs when processes hold resources."
        )
        self.mock_service.create_document.return_value = Path("C:/Users/User/Documents/NOVA/OS_Deadlocks_Notes.docx")

        task = TaskRequest(
            intent="note_generation",
            parameters={"topic": "Operating System Deadlocks"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertTrue(res.success)
        self.assertIn("OS_Deadlocks_Notes.docx", res.output)

    def test_provider_failure_handling(self):
        self.mock_provider.generate.return_value = "[!] Ollama connection failed."
        task = TaskRequest(
            intent="assignment_generation",
            parameters={"topic": "Machine Learning"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("LLM_GENERATION_FAILED", res.error)
        self.mock_service.create_document.assert_not_called()

    def test_doc_service_failure_handling(self):
        self.mock_provider.generate.return_value = "# TITLE: Test Doc\nSome content"
        self.mock_service.create_document.side_effect = PermissionError("Access denied")

        task = TaskRequest(
            intent="readme_generation",
            parameters={"topic": "Python Project"},
            source=InputSource.TEXT,
        )

        res = self.agent.process_task(task)
        self.assertFalse(res.success)
        self.assertIn("DOCUMENT_CREATION_FAILED", res.error)


if __name__ == "__main__":
    unittest.main()