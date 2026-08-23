import unittest
import tempfile
from pathlib import Path
from productivity.preference_store import PreferenceStore


class TestPreferenceStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) / "test_prefs.json"
        self.store = PreferenceStore(storage_path=self.temp_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_set_and_get_preference(self):
        key = self.store.set_preference("preferred_language", "Python")
        self.assertEqual(key, "preferred_language")

        val = self.store.get_preference("preferred_language")
        self.assertEqual(val, "Python")

    def test_delete_preference(self):
        self.store.set_preference("theme", "dark")
        self.assertTrue(self.store.delete_preference("theme"))
        self.assertIsNone(self.store.get_preference("theme"))

    def test_empty_key_raises(self):
        with self.assertRaises(ValueError):
            self.store.set_preference("  ", "value")


if __name__ == "__main__":
    unittest.main()