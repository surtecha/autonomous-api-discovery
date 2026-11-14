"""Validate generated clients against fresh loopback targets inside networkless containers."""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path

from scripts.paths import workspace_path
from scripts.test_sandbox import run, validation_passed


def validate(directory: Path, kind: str) -> dict[str, object]:
    directory = workspace_path(directory)
    baseline = run(directory)
    if not validation_passed(baseline):
        raise RuntimeError("SDK must pass restricted baseline checks before live validation")
    name = "discovery-live-" + uuid.uuid4().hex
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network=none",
        "--read-only",
        "--user=65532:65532",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory=256m",
        "--cpus=1",
        "--pids-limit=64",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
        "--env=HOME=/tmp",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        f"--env=SDK_KIND={kind}",
        "--mount",
        f"type=bind,src={directory},dst=/artifacts,readonly",
        "--mount",
        f"type=bind,src={Path('targets').resolve()},dst=/target/targets,readonly",
        "--mount",
        f"type=bind,src={Path('tests/container').resolve()},dst=/checks,readonly",
        "api-discovery-validator:local",
        "python",
        "-c",
        (
            "import subprocess,json,sys,xml.etree.ElementTree as E; "
            "result=subprocess.run(['python','-m','pytest','-p','no:cacheprovider','-q',"
            "'--tb=short','--junitxml=/tmp/live.xml','/checks/sdk_workflows.py'],capture_output=True); "
            "suites=list(E.parse('/tmp/live.xml').getroot().iter('testsuite')); "
            "counts={k:sum(int(s.get(k,0)) for s in suites) for k in "
            "['tests','failures','errors','skipped']}; "
            "print(json.dumps({'test_counts':counts,'output':result.stdout.decode(errors='replace')})); "
            "sys.exit(result.returncode or int(counts['tests']==0 or any(counts[k] for k in "
            "['failures','errors','skipped'])))"
        ),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, timeout=60, check=False)
        try:
            details = json.loads(completed.stdout)
        except (ValueError, UnicodeDecodeError):
            details = {"output": "Live validator failed before reporting test counts"}
        result: dict[str, object] = {
            "target": kind,
            "status": "passed" if completed.returncode == 0 else "failed",
            "transport": "container_loopback_http",
            "external_network": False,
            **details,
            "baseline": baseline,
        }
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15, check=False)
        result = {"target": kind, "status": "timeout"}
    (directory.parent / "live-sdk.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path("experiments/reports/fixture-diagnostics")
    )
    args = parser.parse_args()
    results = [
        validate(args.root / kind / "gain" / "sdk", kind)
        for kind in ("ecommerce", "subscriptions", "warehouse", "complex")
    ]
    print(json.dumps(results, indent=2))
    return 0 if all(result["status"] == "passed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
