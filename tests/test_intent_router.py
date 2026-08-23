import unittest
from unittest.mock import patch
from core.intent_router import IntentRouter, InputSource, TaskRequest
from core.tool_registry import initialize_default_registry


class TestIntentRouter(unittest.TestCase):

    def setUp(self):
        self.router = IntentRouter()
        self.registry = initialize_default_registry()

    def test_open_app_routing(self):
        res = self.router.route("open vscode", source=InputSource.TEXT)
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "open_application")
        self.assertEqual(res.task_request.parameters["app_name"], "vscode")
        self.assertEqual(res.task_request.source, InputSource.TEXT)

    def test_set_volume_routing(self):
        res = self.router.route("set volume to 50", source=InputSource.VOICE)
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "set_volume")
        self.assertEqual(res.task_request.parameters["level"], 50)
        self.assertEqual(res.task_request.source, InputSource.VOICE)

    def test_invalid_volume_bounds(self):
        res = self.router.route("set volume to 150")
        self.assertFalse(res.success)
        self.assertIn("out of bounds", res.error)

    def test_mute_and_unmute_routing(self):
        mute_res = self.router.route("mute audio")
        self.assertTrue(mute_res.success)
        self.assertTrue(mute_res.task_request.parameters["mute"])

        unmute_res = self.router.route("unmute audio")
        self.assertTrue(unmute_res.success)
        self.assertFalse(unmute_res.task_request.parameters["mute"])

    def test_screenshot_routing(self):
        res = self.router.route("take a screenshot")
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "take_screenshot")

    def test_reminder_routing(self):
        res = self.router.route("remind me in 5 minutes to submit assignment")
        self.assertTrue(res.success)
        self.assertEqual(res.task_request.intent, "create_reminder")

    def test_unknown_intent(self):
        res = self.router.route("tell me about quantum computing")
        self.assertFalse(res.success)
        self.assertIn("UNSUPPORTED", res.error)

    @patch("os.system")
    def test_router_execution_boundary_with_registry(self, mock_os_system):
        res = self.router.route("open vscode")
        self.assertTrue(res.success)
        tool_res = self.registry.execute(res.task_request.intent, **res.task_request.parameters)
        self.assertTrue(tool_res.success)
        mock_os_system.assert_called_once_with("start code")


if __name__ == "__main__":
    unittest.main()