import unittest
from unittest.mock import MagicMock, patch
from core.assistant import NovaAssistant
from core.intent_router import InputSource
from core.tool_registry import default_registry


class TestPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MagicMock()
        self.assistant = NovaAssistant(provider=self.mock_provider)

    @patch("os.system")
    def test_end_to_end_open_app_text(self, mock_os_system):
        response = self.assistant.process_message("open vscode", source=InputSource.TEXT)
        self.assertIn("Opening", response)
        mock_os_system.assert_called_once_with("start code")

    def test_end_to_end_set_volume_voice(self):
        # Patch the registered tool function on the default registry instance
        tool = default_registry.get("set_volume")
        with patch.object(tool, "func", return_value="Volume set to 40 percent, Boss."):
            mock_tts = MagicMock()

            response = self.assistant.process_message(
                "set volume to 40",
                source=InputSource.VOICE,
                tts_engine=mock_tts,
            )

            self.assertIn("Volume set to 40", response)
            mock_tts.speak.assert_called_once_with(response)

    def test_conversational_fallback_does_not_execute_tools(self):
        # 1st call: LLMIntentRouter -> returns non-tool JSON / unknown
        # 2nd call: Conversational Fallback -> returns answer text
        self.mock_provider.generate.side_effect = [
            '{"intent": "unknown", "parameters": {}}',
            "A deadlock occurs when processes hold resources while waiting for others.",
        ]

        response = self.assistant.process_message(
            "Explain deadlock in operating systems.",
            source=InputSource.TEXT,
        )

        self.assertIn("deadlock", response.lower())
        self.assertEqual(self.mock_provider.generate.call_count, 2)

    @patch("os.system")
    def test_tts_not_invoked_for_text_input(self, mock_os_system):
        mock_tts = MagicMock()
        response = self.assistant.process_message("open vscode", source=InputSource.TEXT, tts_engine=mock_tts)
        mock_tts.speak.assert_not_called()


if __name__ == "__main__":
    unittest.main()