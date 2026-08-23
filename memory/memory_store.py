import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
from memory.memory_models import SessionData, Message


class MemoryStore(ABC):
    """Abstract interface for local memory persistence."""

    @abstractmethod
    def save_session(self, session: SessionData) -> None:
        pass

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[SessionData]:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def clear_all(self) -> None:
        pass


class LocalJSONMemoryStore(MemoryStore):
    """
    Lightweight, offline-first local JSON file storage for session memory.
    Saves sessions under Path.home() / 'Documents' / 'NOVA' / 'memory.json'.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            self.storage_path = Path.home() / "Documents" / "NOVA" / "memory.json"
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
            raise RuntimeError(f"Failed to persist memory store: {e}")

    def save_session(self, session: SessionData) -> None:
        data = self._read_data()
        data[session.session_id] = session.to_dict()
        self._write_data(data)

    def load_session(self, session_id: str) -> Optional[SessionData]:
        data = self._read_data()
        raw_session = data.get(session_id)
        if raw_session:
            return SessionData.from_dict(raw_session)
        return None

    def delete_session(self, session_id: str) -> bool:
        data = self._read_data()
        if session_id in data:
            del data[session_id]
            self._write_data(data)
            return True
        return False

    def clear_all(self) -> None:
        self._write_data({})