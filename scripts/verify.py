"""Reproduce the local release gate against the real Compose stack."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL

from scripts.test_sandbox import run, validation_passed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--database-port", type=int, default=15432)
    args = parser.parse_args()
    values = {
        key: value for key, value in dotenv_values(args.env_file).items() if value is not None
    }
    for name in ("POSTGRES_PASSWORD", "BACKEND_API_TOKEN", "WEB_USERNAME", "WEB_PASSWORD"):
        if not values.get(name):
            parser.error(f"{name} must be configured in the environment file")
    root = Path(".runtime/verification")
    root.mkdir(parents=True, exist_ok=True)
    override = root / "compose.yml"
    override.write_text(
        'services:\n  postgres:\n    ports: ["127.0.0.1:'
        + str(args.database_port)
        + ':5432"]\n    networks: [control, ingress]\n'
    )
    env = (
        os.environ
        | values
        | {
            "DATABASE_URL": URL.create(
                "postgresql+psycopg",
                username="discovery",
                password=values["POSTGRES_PASSWORD"],
                host="127.0.0.1",
                port=args.database_port,
                database="discovery",
            ).render_as_string(hide_password=False),
            "RUN_SANDBOX_TESTS": "1",
            "E2E_EXTERNAL_SERVER": "1",
            "E2E_BASE_URL": "http://127.0.0.1:" + values.get("WEB_PORT", "3000"),
        }
    )
    checks: dict[str, str] = {}

    def report(status: str) -> None:
        (root / "release-checks.json").write_text(
            json.dumps({"status": status, "checks": checks}, indent=2) + "\n"
        )

    report("running")

    def check(name: str, command: list[str], cwd: str = ".") -> None:
        print(f"Checking {name}", flush=True)
        started = time.monotonic()
        try:
            subprocess.run(command, cwd=cwd, env=env, check=True)
        except subprocess.CalledProcessError:
            checks[name] = "failed"
            report("failed")
            raise
        checks[name] = f"passed ({time.monotonic() - started:.1f}s)"
        report("running")

    compose = [
        "docker",
        "compose",
        "--env-file",
        str(args.env_file),
        "-f",
        "docker-compose.yml",
        "-f",
        str(override),
    ]
    check("compose", [*compose, "up", "--build", "-d"])
    request = urllib.request.Request(
        "http://127.0.0.1:" + values.get("API_PORT", "8000") + "/api/v1/readiness",
        headers={"Authorization": "Bearer " + values["BACKEND_API_TOKEN"]},
    )
    for _ in range(60):
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                if response.status == 200:
                    break
        except (OSError, urllib.error.URLError):
            time.sleep(1)
    else:
        raise RuntimeError("Compose readiness deadline exceeded")
    python = sys.executable
    check(
        "validator image",
        [
            "docker",
            "build",
            "-f",
            "infrastructure/docker/validator.Dockerfile",
            "-t",
            "api-discovery-validator:local",
            ".",
        ],
    )
    check("python tests", [python, "-m", "pytest", "-q", "--tb=short"])
    check("python lint", ["ruff", "check", "packages", "apps/api", "scripts", "tests", "targets"])
    check("python types", ["mypy", "packages", "apps/api"])
    check(
        "full-stack smoke", [python, "-m", "scripts.smoke_stack", "--env-file", str(args.env_file)]
    )
    for name in ("lint", "typecheck", "build", "test:e2e"):
        check("frontend " + name, ["npm", "run", name], "apps/web")
    check("fixture diagnostics", [python, "-m", "scripts.fixture_diagnostics"])
    measured_diagnostics = []
    for directory in sorted(Path("experiments/reports/fixture-diagnostics").glob("*/*/sdk")):
        if not validation_passed(run(directory)):
            checks["12 fixture SDK bundles"] = "failed"
            report("failed")
            raise RuntimeError(f"Restricted SDK validation failed: {directory}")
        diagnostics_path = directory.parent / "diagnostics.json"
        diagnostics = json.loads(diagnostics_path.read_text())
        diagnostics["validation"] = json.loads((directory / "validation.json").read_text())
        diagnostics["sdk_test_pass_rate"] = 1.0  # Reached only with nonzero, all-passing counts.
        diagnostics_path.write_text(json.dumps(diagnostics, indent=2) + "\n")
        measured_diagnostics.append({"target": directory.parent.parent.name, **diagnostics})
    Path("experiments/reports/fixture-diagnostics/summary.json").write_text(
        json.dumps(measured_diagnostics, indent=2) + "\n"
    )
    checks["12 fixture SDK bundles"] = "passed"
    check("live SDK workflows", [python, "-m", "scripts.live_sdk"])
    check("HTTP benchmarks", [python, "-m", "scripts.benchmark"])
    check("artifact consistency", [python, "-m", "scripts.validate_artifact_structure"])
    check("security analysis", ["bandit", "-r", "packages", "apps/api", "-ll"])
    check("Python dependency audit", ["pip-audit", "--progress-spinner", "off"])
    check("frontend dependency audit", ["npm", "audit", "--audit-level=moderate"], "apps/web")
    check("secret pattern scan", [python, "-m", "scripts.security_scan"])
    check("release secret scanners", [python, "-m", "scripts.scan_secrets"])
    report("passed")
    shutil.copyfile(root / "release-checks.json", "experiments/reports/release-checks.json")
    print(
        "Release checks passed. Stack remains running; credentials remain in the environment file."
    )


if __name__ == "__main__":
    main()
