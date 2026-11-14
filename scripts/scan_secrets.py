"""Scan exactly the Git release inputs, including untracked files and staged ignored files."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    root = Path.cwd().resolve()
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True,
        check=True,
    )
    files = sorted({path for path in listing.stdout.decode().split("\0") if path})
    if not files:
        raise RuntimeError("No release files found to scan")
    with tempfile.TemporaryDirectory(prefix="api-discovery-release-scan-") as temporary:
        exported = Path(temporary)
        for name in files:
            source = root / name
            if source.is_symlink() or not source.resolve().is_relative_to(root):
                raise ValueError("Release input symlinks and external paths require review")
            if not source.is_file():
                continue  # A staged deletion has no worktree content to export.
            destination = exported / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        detection = subprocess.run(
            [
                "detect-secrets",
                "scan",
                "--all-files",
                "--no-verify",
                # Content hashes identify downloaded artifacts, not credentials.
                "--exclude-lines",
                r'^\s*"(?:digest|runtime_archive_sha256)": "(?:sha256:)?[0-9a-f]{64}",?$',
                "--exclude-files",
                r"package-lock\.json$|requirements(-dev|-validator)?\.lock$",
                ".",
            ],
            cwd=exported,
            capture_output=True,
            text=True,
            check=True,
        )
        findings = [
            {
                "file": name,
                "line": item["line_number"],
                "scanner": "detect-secrets",
                "category": item["type"],
            }
            for name, items in json.loads(detection.stdout)["results"].items()
            for item in items
        ]
        report = exported / "gitleaks-results.json"
        leak_scan = subprocess.run(
            [
                "gitleaks",
                "dir",
                ".",
                "--config",
                str(root / ".gitleaks.toml"),
                "--redact",
                "--no-banner",
                "--report-format",
                "json",
                "--report-path",
                str(report),
            ],
            cwd=exported,
            capture_output=True,
            check=False,
        )
        if leak_scan.returncode not in {0, 1} or not report.exists():
            raise RuntimeError("Gitleaks did not complete successfully")
        findings.extend(
            {
                "file": item["File"],
                "line": item["StartLine"],
                "scanner": "gitleaks",
                "category": item["RuleID"],
            }
            for item in json.loads(report.read_text())
        )
    result = {
        "files_scanned": len(files),
        "findings": findings,
        "status": "failed" if findings else "passed",
    }
    destination = root / ".runtime/verification"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "secrets.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
