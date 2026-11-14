import os
import subprocess
import sys
import unittest
from pathlib import Path

from test_support import temporary_directory


class LocalSetupTests(unittest.TestCase):
    def test_credentials_are_private_and_existing_configuration_is_preserved(self):
        script = Path("scripts/setup_local.py").resolve()
        with temporary_directory() as folder:
            command = [sys.executable, str(script), "--api-port", "18000", "--web-port", "13000"]
            first = subprocess.run(command, cwd=folder, capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0)
            path = Path(folder) / ".env"
            original = path.read_text()
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertIn("WEB_ORIGIN=http://127.0.0.1:13000", original)
            self.assertNotIn(original.split("WEB_PASSWORD=")[1].splitlines()[0], first.stdout)
            second = subprocess.run(command, cwd=folder, capture_output=True, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(path.read_text(), original)
