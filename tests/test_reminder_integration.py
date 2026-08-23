import unittest
from core.assistant import NovaAssistant
from core.intent_router import InputSource


class TestReminderIntegration(unittest.TestCase):

    def setUp(self):
        self.assistant = NovaAssistant()

    def tearDown(self):
        if hasattr(self.assistant, "shutdown"):
            self.assistant.shutdown()

    def test_create_and_list_reminder_pipeline(self):
        res = self.assistant.process_turn(
            "remind me in 10 minutes to submit assignment",
            source=InputSource.TEXT,
        )
        self.assertIn("Set reminder", res)

        list_res = self.assistant.process_turn(
            "show my reminders",
            source=InputSource.TEXT,
        )
        self.assertIn("reminders", list_res.lower())


if __name__ == "__main__":
    unittest.main()