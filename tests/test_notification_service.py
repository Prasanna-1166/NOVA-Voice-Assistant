import unittest
from services.notification_service import NotificationService


class TestNotificationService(unittest.TestCase):

    def test_notify_with_valid_message(self):
        success = NotificationService.notify("Test Title", "Test Message Payload")
        self.assertTrue(success)

    def test_notify_with_empty_message(self):
        success = NotificationService.notify("Test Title", "")
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
    