import sys
import importlib
import logging

logger = logging.getLogger("NOVA.NotificationService")


class NotificationService:
    """
    Local notification service responsible for delivering triggered reminders.
    Supports Windows Toast notifications and console output gracefully.
    """

    @staticmethod
    def notify(title: str, message: str) -> bool:
        """
        Presents a local alert notification without crashing if notification libraries are missing.
        """
        if not message:
            return False

        # Always output to console
        print(f"\n[🔔 REMINDER NOTIFICATION]: {title} - {message}\n")

        # Attempt OS-level native desktop notification safely
        try:
            if sys.platform == "win32":
                try:
                    win10toast = importlib.import_module("win10toast")
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                    return True
                except Exception:
                    pass

            try:
                plyer = importlib.import_module("plyer")
                plyer.notification.notify(
                    title=title,
                    message=message,
                    app_name="NOVA Assistant",
                    timeout=5,
                )
                return True
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Desktop notification fallback used: {e}")

        return True


default_notification_service = NotificationService()