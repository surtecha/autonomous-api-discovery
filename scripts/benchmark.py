"""Real loopback HTTP benchmarks with a fresh target process per run."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

from scripts.paths import workspace_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("experiments/reports/http"))
    args = parser.parse_args()
    args.output = workspace_path(args.output)
    args.output.mkdir(parents=True, exist_ok=True)
    for kind in ("ecommerce", "subscriptions", "warehouse", "complex"):
        for strategy in ("fifo", "random", "gain"):
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            output = args.output / kind / strategy
            output.mkdir(parents=True, exist_ok=True)
            policy = json.loads(Path(f"experiments/configs/{kind}.json").read_text())
            policy["origin"] = f"http://127.0.0.1:{port}"
            config = output / "policy.json"
            config.write_text(json.dumps(policy, indent=2) + "\n")
            process = subprocess.Popen(
                [sys.executable, "-m", "targets.service", kind, "--port", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                ready = False
                for _ in range(40):
                    if process.poll() is not None:
                        raise RuntimeError("Target process failed to start")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            ready = True
                            break
                    except OSError:
                        time.sleep(0.1)
                if not ready:
                    raise RuntimeError("Target startup deadline exceeded")
                command = [
                    sys.executable,
                    "-m",
                    "scripts.discover",
                    "--config",
                    str(config),
                    "--output",
                    str(output),
                    "--strategy",
                    strategy,
                    "--session",
                    str(uuid.uuid4()),
                ]
                started = time.monotonic()
                subprocess.run(command, check=True, timeout=150)
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "scripts.evaluate",
                        "--knowledge",
                        str(output / "knowledge.json"),
                        "--truth",
                        f"targets/ground_truth/{kind}.json",
                        "--output",
                        str(output / "evaluation.json"),
                    ],
                    check=True,
                    timeout=10,
                )
                subprocess.run(
                    [sys.executable, "-m", "scripts.test_sandbox", str(output / "sdk")],
                    check=True,
                    timeout=420,
                )
                validation = json.loads((output / "sdk" / "validation.json").read_text())
                counts = validation.get("test_counts")
                if counts and counts["tests"]:
                    score_path = output / "evaluation.json"
                    score = json.loads(score_path.read_text())
                    score["sdk_test_pass_rate"] = (
                        counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
                    ) / counts["tests"]
                    score_path.write_text(json.dumps(score, indent=2) + "\n")
                metadata = {
                    "transport": "loopback_http",
                    "fresh_target": True,
                    "elapsed_seconds": time.monotonic() - started,
                }
                (output / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    summary = []
    for kind in ("ecommerce", "subscriptions", "warehouse", "complex"):
        for strategy in ("fifo", "random", "gain"):
            directory = args.output / kind / strategy
            summary.append(
                {
                    "target": kind,
                    "strategy": strategy,
                    "evaluation": json.loads((directory / "evaluation.json").read_text()),
                    "validation": json.loads((directory / "sdk/validation.json").read_text()),
                    "run": json.loads((directory / "run.json").read_text()),
                }
            )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
