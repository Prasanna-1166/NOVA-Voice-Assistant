import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from productivity.task_models import Task, TaskStatus, TaskPriority


class TaskStore:
    """
    Lightweight, local JSON-based persistent storage for structured user tasks/to-dos.
    Saves to Path.home() / 'Documents' / 'NOVA' / 'tasks.json'.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            self.storage_path = Path.home() / "Documents" / "NOVA" / "tasks.json"
        else:
            self.storage_path = storage_path

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_data(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return {}
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write_data(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to write task store: {e}")

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "MEDIUM",
        due_at: Optional[float] = None,
    ) -> Task:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")

        try:
            p_enum = TaskPriority(priority.upper())
        except ValueError:
            p_enum = TaskPriority.MEDIUM

        task = Task(
            title=clean_title,
            description=description,
            priority=p_enum,
            due_at=due_at,
        )

        data = self._read_data()
        data[task.id] = task.to_dict()
        self._write_data(data)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        data = self._read_data()
        raw = data.get(task_id)
        if raw:
            return Task.from_dict(raw)
        return None

    def find_task_by_identifier(self, identifier: str) -> Optional[Task]:
        """Find task by exact ID or case-insensitive title match."""
        data = self._read_data()
        if identifier in data:
            return Task.from_dict(data[identifier])

        clean_id = identifier.lower().strip()
        for raw in data.values():
            t = Task.from_dict(raw)
            if t.title.lower().strip() == clean_id or t.id.lower() == clean_id:
                return t
        return None

    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        data = self._read_data()
        tasks = [Task.from_dict(raw) for raw in data.values()]

        if status:
            try:
                s_enum = TaskStatus(status.upper())
                tasks = [t for t in tasks if t.status == s_enum]
            except ValueError:
                pass

        return sorted(tasks, key=lambda x: x.created_at, reverse=True)

    def list_pending_tasks(self) -> List[Task]:
        return self.list_tasks(status="PENDING")

    def list_completed_tasks(self) -> List[Task]:
        return self.list_tasks(status="COMPLETED")

    def complete_task(self, identifier: str) -> Optional[Task]:
        task = self.find_task_by_identifier(identifier)
        if not task:
            return None

        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()

        data = self._read_data()
        data[task.id] = task.to_dict()
        self._write_data(data)
        return task

    def update_task(
        self,
        identifier: str,
        title: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Task]:
        task = self.find_task_by_identifier(identifier)
        if not task:
            return None

        if title and title.strip():
            task.title = title.strip()

        if priority:
            try:
                task.priority = TaskPriority(priority.upper())
            except ValueError:
                pass

        if status:
            try:
                task.status = TaskStatus(status.upper())
                if task.status == TaskStatus.COMPLETED and not task.completed_at:
                    task.completed_at = time.time()
            except ValueError:
                pass

        data = self._read_data()
        data[task.id] = task.to_dict()
        self._write_data(data)
        return task

    def delete_task(self, identifier: str) -> bool:
        task = self.find_task_by_identifier(identifier)
        if not task:
            return False

        data = self._read_data()
        if task.id in data:
            del data[task.id]
            self._write_data(data)
            return True
        return False

    def clear_tasks(self) -> None:
        self._write_data({})


default_task_store = TaskStore()