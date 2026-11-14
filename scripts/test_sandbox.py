"""Execute deterministic generated tests in a restricted, networkless container."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

CHECKS = ("sdk_tests", "sdk_lint", "sdk_types", "sdk_packaging")


def validation_passed(results: dict[str, object]) -> bool:
    counts = results.get("test_counts")
    return (
        all(results.get(name) == "passed" for name in CHECKS)
        and isinstance(counts, dict)
        and type(counts.get("tests")) is int
        and counts["tests"] > 0
        and all(
            type(counts.get(key)) is int and counts[key] == 0
            for key in ("failures", "errors", "skipped")
        )
    )


def run(directory: Path) -> dict[str, object]:
    if directory.is_symlink():
        raise ValueError("Artifact symlinks are forbidden")
    directory = directory.resolve(strict=True)
    workspace = Path.cwd().resolve()
    if not directory.is_relative_to(workspace) or directory.is_symlink():
        raise ValueError("Artifact directory must be inside the workspace")
    required = {"client.py", "test_client.py", "fixtures.json", "openapi.json", "pyproject.toml"}
    entries = list(directory.iterdir())
    if not required.issubset({path.name for path in entries}) or any(
        path.is_symlink() or not path.is_file() or path.name not in required | {"validation.json"}
        for path in entries
    ):
        raise ValueError("Only generated SDK bundle files may enter the validator")
    results: dict[str, object] = {}
    checks = {
        "sdk_tests": [
            "python",
            "-c",
            "import subprocess,json,sys,xml.etree.ElementTree as E; result=subprocess.run(['python','-m','pytest','-p','no:cacheprovider','-q','--junitxml=/tmp/results.xml','test_client.py'],capture_output=True); root=E.parse('/tmp/results.xml').getroot(); suites=list(root.iter('testsuite')); counts={key:sum(int(s.get(key,0)) for s in suites) for key in ['tests','failures','errors','skipped']}; print(json.dumps(counts)); sys.exit(result.returncode)",
        ],
        "sdk_lint": ["ruff", "check", "--no-cache", "client.py"],
        "sdk_types": ["mypy", "--strict", "--cache-dir=/tmp/mypy", "client.py"],
        "sdk_packaging": [
            "python",
            "-c",
            "import shutil,subprocess; shutil.copytree('/artifacts','/tmp/package'); subprocess.run(['python','-m','build','--no-isolation','--outdir','/tmp/dist'],cwd='/tmp/package',check=True)",
        ],
    }
    try:
        daemon = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        available = daemon.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        available = False
    if not available:
        results = {name: "unavailable_docker" for name in checks}
        results["test_counts"] = None
        path = directory / "validation.json"
        validation = json.loads(path.read_text()) if path.exists() else {}
        validation.update(results)
        path.write_text(json.dumps(validation, indent=2) + "\n")
        return results
    for name, command in checks.items():
        container_name = "discovery-check-" + uuid.uuid4().hex
        invocation = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network=none",
            "--read-only",
            "--user=65532:65532",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory=256m",
            "--cpus=1",
            "--pids-limit=64",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--mount",
            f"type=bind,src={directory},dst=/artifacts,readonly",
            "--workdir=/artifacts",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=HOME=/tmp",
            "api-discovery-validator:local",
            *command,
        ]
        try:
            completed = subprocess.run(invocation, capture_output=True, timeout=90, check=False)
            results[name] = (
                "passed"
                if completed.returncode == 0
                else ("container_start_failed" if completed.returncode == 125 else "failed")
            )
            if name == "sdk_tests":
                try:
                    counts = json.loads(completed.stdout)
                    if isinstance(counts, dict) and all(
                        type(counts.get(key)) is int
                        for key in ("tests", "failures", "errors", "skipped")
                    ):
                        results["test_counts"] = {
                            key: counts[key] for key in ("tests", "failures", "errors", "skipped")
                        }
                except (ValueError, UnicodeDecodeError):
                    results["test_counts"] = None
        except FileNotFoundError:
            results[name] = "unavailable_docker"
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["docker", "rm", "-f", container_name], capture_output=True, timeout=15, check=False
            )
            results[name] = "timeout"
    path = directory / "validation.json"
    validation = json.loads(path.read_text()) if path.exists() else {}
    validation.update(results)
    path.write_text(json.dumps(validation, indent=2) + "\n")
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    results = run(args.directory)
    print(json.dumps(results))
    return 0 if validation_passed(results) else 1


if __name__ == "__main__":
    sys.exit(main())
