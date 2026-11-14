"""Constrain CLI artifact paths to the project workspace."""

from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def workspace_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(WORKSPACE):
        raise ValueError("Path must remain inside the project workspace")
    return resolved
