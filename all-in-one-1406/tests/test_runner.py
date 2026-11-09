import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import execute, classify

SHA = "a" * 64

class RunnerTest(unittest.TestCase):
    def test_classify_fail_closed(self):
        good = {"source_id": "SGK_B001_K1_E01", "lesson_id": "B001", "owner_batch": "BQA-01",
                "track": "SGK", "volume": "1", "pdf_page": "7", "source_sha256": SHA}
        self.assertEqual(classify(good)[0], "SOURCE_PROCESSING_REQUIRED")
        self.assertEqual(classify({**good, "pdf_page": ""})[0], "INPUT_EXCEPTION")

    def test_resume_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "source.csv"
            with manifest.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["source_id","lesson_id","owner_batch","track","volume","pdf_page","source_sha256"])
                writer.writeheader()
                writer.writerow({"source_id":"SGK_B001_K1_E01","lesson_id":"B001","owner_batch":"BQA-01","track":"SGK","volume":"1","pdf_page":"7","source_sha256":SHA})
            state = root / "state"
            first = execute(manifest, state)
            second = execute(manifest, state)
            self.assertEqual(first["total"], 1)
            self.assertEqual(second["total"], 1)
            self.assertEqual(second["source_verified"], 0)
            db = sqlite3.connect(state / "state.sqlite3")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 1)
            db.close()
            execute(manifest, state, retry=True)
            db = sqlite3.connect(state / "state.sqlite3")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 2)
            db.close()

if __name__ == "__main__":
    unittest.main()
