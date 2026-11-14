"""Keep disposable test artifacts inside the authorized project workspace."""

import tempfile
from pathlib import Path


def temporary_directory() -> tempfile.TemporaryDirectory[str]:
    root = Path(__file__).resolve().parents[1] / ".runtime" / "test-tmp"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)
