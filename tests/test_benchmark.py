"""Report preservation and comparison integrity checks."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.benchmark import main


class BenchmarkPreservationTests(unittest.TestCase):
    def test_existing_output_is_rejected_before_starting_targets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sentinel = root / "summary.json"
            sentinel.write_text("existing successful report\n")
            with (
                patch("sys.argv", ["benchmark", "--output", str(root)]),
                patch("scripts.benchmark.workspace_path", return_value=root),
                patch("scripts.benchmark.subprocess.Popen") as start,
                self.assertRaises(FileExistsError),
            ):
                main()
            start.assert_not_called()
            self.assertEqual(sentinel.read_text(), "existing successful report\n")
