"""Snapshot installed dependency closures without installing outside Conda."""

from __future__ import annotations

import tomllib
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def closure(requirements: list[str]) -> dict[str, str]:
    pending = [Requirement(value) for value in requirements]
    visited: set[tuple[str, tuple[str, ...]]] = set()
    versions: dict[str, str] = {}
    while pending:
        requirement = pending.pop()
        if requirement.marker and not requirement.marker.evaluate():
            continue
        name = canonicalize_name(requirement.name)
        extras = tuple(sorted(requirement.extras))
        identity = (name, extras)
        if identity in visited:
            continue
        visited.add(identity)
        installed = distribution(name)
        if installed.version not in requirement.specifier:
            raise ValueError(f"Installed dependency does not satisfy requirement: {name}")
        versions[name] = installed.version
        for child in installed.requires or []:
            parsed = Requirement(child)
            if parsed.marker is None or any(
                parsed.marker.evaluate({"extra": extra}) for extra in ("", *extras)
            ):
                # The marker was evaluated for the parent's extras above.
                parsed.marker = None
                pending.append(parsed)
    return versions


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())
    runtime = project["project"]["dependencies"]
    development = (
        runtime
        + project["project"]["optional-dependencies"]["dev"]
        + project["build-system"]["requires"]
        + ["wheel"]
    )
    for filename, requirements in (
        ("requirements.lock", runtime),
        ("requirements-dev.lock", development),
        (
            "requirements-validator.lock",
            [
                "httpx",
                "pydantic",
                "pytest",
                "ruff",
                "mypy",
                "build",
                "setuptools",
                "wheel",
                "jsonschema",
            ],
        ),
    ):
        versions = closure(requirements)
        header = "# Installed Python 3.12 dependency snapshot. Exact versions, without artifact hashes.\n"
        (root / filename).write_text(
            header + "".join(f"{name}=={version}\n" for name, version in sorted(versions.items()))
        )
        print(f"{filename}: {len(versions)} dependencies")


if __name__ == "__main__":
    main()
