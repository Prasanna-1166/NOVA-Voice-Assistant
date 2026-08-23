import os
import time
from typing import Optional, Any
from productivity.task_store import default_task_store, TaskStore
from productivity.preference_store import default_preference_store, PreferenceStore
from scheduling.reminder_store import default_reminder_store, ReminderStore


class SystemTools:

    # --- Productivity Tools ---
    @staticmethod
    def open_application(app_name: str) -> str:
        app_map = {
            "vscode": "code",
            "vs code": "code",
            "chrome": "chrome",
            "notepad": "notepad",
            "calculator": "calc",
        }
        cmd = app_map.get(app_name.lower(), app_name)
        os.system(f"start {cmd}")
        return f"Opening {app_name}, Boss."

    # Legacy alias for older unit tests
    open_app = open_application

    @staticmethod
    def set_volume(level: int) -> str:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level} percent, Boss."

    @staticmethod
    def mute_audio(mute: bool = True) -> str:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMute(int(mute), None)
        state = "muted" if mute else "unmuted"
        return f"Audio {state}, Boss."

    @staticmethod
    def take_screenshot() -> str:
        import mss
        from pathlib import Path

        save_dir = Path.home() / "Pictures" / "NOVA_Screenshots"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = save_dir / f"screenshot_{int(time.time())}.png"

        with mss.mss() as sct:
            sct.shot(output=str(filename))
        return f"Screenshot saved to {filename}, Boss."

    @staticmethod
    def process_command(command: str, tts_engine=None, assistant_engine=None):
        return False, ""

    # --- Phase 11 Task Tools ---
    @staticmethod
    def create_task(title: str, description: str = "", priority: str = "MEDIUM", store: Optional[TaskStore] = None) -> str:
        t_store = store or default_task_store
        task = t_store.create_task(title=title, description=description, priority=priority)
        return f"Added '{task.title}' (Priority: {task.priority.value}) to your tasks, Boss."

    @staticmethod
    def list_tasks(status: str = "PENDING", store: Optional[TaskStore] = None) -> str:
        t_store = store or default_task_store
        tasks = t_store.list_tasks(status=status)
        if not tasks:
            return f"You have no {status.lower()} tasks, Boss."

        items = [f"- [{t.id}] {t.title} (Priority: {t.priority.value})" for t in tasks]
        return f"Your {status.lower()} tasks:\n" + "\n".join(items)

    @staticmethod
    def complete_task(task_identifier: str, store: Optional[TaskStore] = None) -> str:
        t_store = store or default_task_store
        task = t_store.complete_task(task_identifier)
        if not task:
            return f"Task '{task_identifier}' was not found, Boss."
        return f"Marked '{task.title}' as completed, Boss."

    @staticmethod
    def update_task(
        task_identifier: str,
        title: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        store: Optional[TaskStore] = None,
    ) -> str:
        t_store = store or default_task_store
        task = t_store.update_task(task_identifier, title=title, priority=priority, status=status)
        if not task:
            return f"Task '{task_identifier}' was not found, Boss."
        return f"Updated task '{task.title}', Boss."

    @staticmethod
    def delete_task(task_identifier: str, store: Optional[TaskStore] = None) -> str:
        t_store = store or default_task_store
        success = t_store.delete_task(task_identifier)
        if not success:
            return f"Task '{task_identifier}' was not found, Boss."
        return f"Deleted task '{task_identifier}', Boss."

    # --- Phase 11 Preference Tools ---
    @staticmethod
    def set_preference(key: str, value: Any, store: Optional[PreferenceStore] = None) -> str:
        p_store = store or default_preference_store
        clean_key = p_store.set_preference(key, value)
        return f"Set preference '{clean_key}' to '{value}', Boss."

    @staticmethod
    def get_preference(key: str, store: Optional[PreferenceStore] = None) -> str:
        p_store = store or default_preference_store
        val = p_store.get_preference(key)
        if val is None:
            return f"No preference found for '{key}', Boss."
        return f"Your preference for '{key}' is '{val}', Boss."

    # --- Phase 12 Reminder Tools ---
    @staticmethod
    def create_reminder(
        title: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        user_text: Optional[str] = None,
        recurrence: str = "NONE",
        store: Optional[ReminderStore] = None,
        **kwargs,
    ) -> str:
        r_store = store or default_reminder_store

        # Resolve title from provided arguments
        rem_title = title or user_text or kwargs.get("message") or "General Reminder"

        # Resolve scheduled time
        rem_time = scheduled_time or kwargs.get("time")
        if not rem_time:
            from datetime import datetime, timedelta
            # Fallback time: 15 minutes from now if time extraction was ambiguous
            rem_time = (datetime.now() + timedelta(minutes=15)).isoformat()

        rem = r_store.create_reminder(title=rem_title, scheduled_time=rem_time, recurrence=recurrence)
        rec_str = f" (Recurrence: {rem.recurrence.value})" if rem.recurrence.value != "NONE" else ""
        return f"Set reminder for '{rem.title}' at {rem.scheduled_time}{rec_str}, Boss."

    @staticmethod
    def list_reminders(status: str = "PENDING", store: Optional[ReminderStore] = None) -> str:
        r_store = store or default_reminder_store
        reminders = r_store.list_reminders(status=status)
        if not reminders:
            return f"You have no {status.lower()} reminders, Boss."

        items = [f"- [{r.id}] '{r.title}' scheduled for {r.scheduled_time}" for r in reminders]
        return f"Your {status.lower()} reminders:\n" + "\n".join(items)

    @staticmethod
    def cancel_reminder(identifier: str, store: Optional[ReminderStore] = None) -> str:
        r_store = store or default_reminder_store
        rem = r_store.cancel_reminder(identifier)
        if not rem:
            return f"Reminder '{identifier}' was not found or is already cancelled, Boss."
        return f"Cancelled reminder '{rem.title}', Boss."

    @staticmethod
    def delete_reminder(identifier: str, store: Optional[ReminderStore] = None) -> str:
        r_store = store or default_reminder_store
        success = r_store.delete_reminder(identifier)
        if not success:
            return f"Reminder '{identifier}' was not found, Boss."
        return f"Deleted reminder '{identifier}', Boss."