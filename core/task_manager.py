import json
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

TASKS_FILE = "tasks.json"

class TaskManager:
    def __init__(self, tts_engine=None):
        self.tts = tts_engine
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.tasks = self._load_tasks()
        self._reschedule_all_reminders()

    def _load_tasks(self):
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"pending": [], "completed": []}

    def _save_tasks(self):
        with open(TASKS_FILE, "w") as f:
            json.dump(self.tasks, f, indent=4)

    def _reschedule_all_reminders(self):
        """Reschedules 30-minute advance warnings on startup."""
        for task in self.tasks["pending"]:
            self._schedule_reminder(task)

    def _schedule_reminder(self, task):
        try:
            target_time = datetime.strptime(task["time"], "%Y-%m-%d %H:%M")
            reminder_time = target_time - timedelta(minutes=30)
            
            # Schedule only if reminder time is in the future
            if reminder_time > datetime.now():
                self.scheduler.add_job(
                    self._trigger_reminder,
                    'date',
                    run_date=reminder_time,
                    args=[task["description"]],
                    id=str(task["id"]),
                    replace_existing=True
                )
        except Exception as e:
            print(f"[!] Scheduling Error: {e}")

    def _trigger_reminder(self, task_desc):
        alert_msg = f"Reminder Boss: You have '{task_desc}' scheduled in 30 minutes."
        print(f"\n[⏰ REMINDER]: {alert_msg}")
        if self.tts:
            self.tts.speak(alert_msg)

    def add_task(self, description: str, date_time_str: str) -> str:
        """Adds a task with time format 'YYYY-MM-DD HH:MM'"""
        task_id = len(self.tasks["pending"]) + len(self.tasks["completed"]) + 1
        new_task = {
            "id": task_id,
            "description": description,
            "time": date_time_str,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.tasks["pending"].append(new_task)
        self._save_tasks()
        self._schedule_reminder(new_task)
        return f"Added task '{description}' set for {date_time_str}. 30-minute reminder scheduled, Boss."

    def complete_task(self, task_id: int) -> str:
        for task in self.tasks["pending"]:
            if task["id"] == task_id:
                self.tasks["pending"].remove(task)
                task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.tasks["completed"].append(task)
                self._save_tasks()
                return f"Task {task_id} marked as completed, Boss."
        return f"Task {task_id} not found in pending list, Boss."

    def get_status(self) -> str:
        pending_count = len(self.tasks["pending"])
        completed_count = len(self.tasks["completed"])
        
        msg = f"You have {pending_count} pending tasks and {completed_count} completed tasks, Boss."
        if pending_count > 0:
            msg += " Pending: " + ", ".join([f"[{t['id']}] {t['description']} at {t['time']}" for t in self.tasks["pending"]])
        return msg