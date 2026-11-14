"""Offline supplemental scan. This does not replace Gitleaks or detect-secrets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXCLUDED = {
    ".git",
    ".conda-envs",
    ".conda-pkgs",
    ".runtime",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    "openai_token": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "credential_url": re.compile(r"(?:https?|postgresql(?:\+psycopg)?)://[^\s:/]+:[^\s@${}]+@"),
}


def scan(root: Path) -> list[dict[str, object]]:
    findings = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if (
            any(part in EXCLUDED for part in relative.parts)
            or not path.is_file()
            or path.is_symlink()
        ):
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            continue
        if path.suffix in {".png", ".zip", ".sqlite", ".pyc"}:
            continue
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        for line, value in enumerate(content.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                if pattern.search(value):
                    if relative.as_posix() == "tests/test_core.py" and "user:pass@" in value:
                        continue
                    findings.append({"path": relative.as_posix(), "line": line, "category": name})
    return findings


if __name__ == "__main__":
    findings = scan(Path.cwd())
    print(json.dumps({"scanner": "supplemental-pattern-scan", "findings": findings}, indent=2))
    sys.exit(bool(findings))
