"""Guard batch-file path passing on Windows.

%~dp0 ends with a backslash. Inside a quoted CLI argument the backslash
can escape the terminal quote for the Windows CRT argv parser. Running
'cd /d "%~dp0"' and then passing "%CD%" avoids that ambiguity.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class BatchPathTests(unittest.TestCase):
    def test_pc_and_canary_pass_unambiguous_root(self):
        for name in ("CHECK_PC.bat","RUN_CANARY.bat"):
            with self.subTest(name=name):
                script=(ROOT/name).read_text(encoding="utf-8")
                self.assertIn('cd /d "%~dp0"',script)
                self.assertIn('--root "%CD%"',script)
                self.assertNotIn('--root "%~dp0"',script)

if __name__=="__main__":
    unittest.main()
