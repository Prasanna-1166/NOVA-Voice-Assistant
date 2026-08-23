import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class PreferenceStore:
    """
    Lightweight, local JSON-based persistent storage for key-value user preferences.
    Saves to Path.home() / 'Documents' / 'NOVA' / 'preferences.json'.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            self.storage_path = Path.home() / "Documents" / "NOVA" / "preferences.json"
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
            raise RuntimeError(f"Failed to write preference store: {e}")

    def set_preference(self, key: str, value: Any) -> str:
        clean_key = key.strip().lower().replace(" ", "_")
        if not clean_key:
            raise ValueError("Preference key cannot be empty.")

        data = self._read_data()
        data[clean_key] = value
        self._write_data(data)
        return clean_key

    def get_preference(self, key: str) -> Optional[Any]:
        clean_key = key.strip().lower().replace(" ", "_")
        data = self._read_data()
        return data.get(clean_key)

    def delete_preference(self, key: str) -> bool:
        clean_key = key.strip().lower().replace(" ", "_")
        data = self._read_data()
        if clean_key in data:
            del data[clean_key]
            self._write_data(data)
            return True
        return False

    def list_preferences(self) -> Dict[str, Any]:
        return self._read_data()

    def clear_preferences(self) -> None:
        self._write_data({})


default_preference_store = PreferenceStore()