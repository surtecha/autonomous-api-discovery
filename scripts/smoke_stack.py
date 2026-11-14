"""Exercise the real API/queue/worker/target/artifact path with disposable sessions."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    values = dotenv_values(args.env_file)
    base = "http://127.0.0.1:" + (values.get("API_PORT") or "8000") + "/api/v1/"

    def request(path: str, body: dict[str, Any] | None = None) -> Any:
        token = values.get("BACKEND_API_TOKEN")
        if not token:
            raise ValueError("BACKEND_API_TOKEN must be configured")
        invocation = urllib.request.Request(
            base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(invocation, timeout=10) as response:
            return json.load(response)

    sessions = [
        request("discovery-sessions", {"target": kind, "budget": 100})
        for kind in ("ecommerce", "subscriptions", "warehouse", "complex", "ecommerce")
    ]
    cancelled = request("discovery-sessions", {"target": "subscriptions", "budget": 100})
    cancellation = request(f"discovery-sessions/{cancelled['id']}/cancel", {})
    if cancellation["status"] != "cancelled":
        raise RuntimeError("Cancellation was not persisted")
    results = []
    for session in sessions:
        prefix = "discovery-sessions/" + session["id"]
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            current = request(prefix)
            if current["status"] not in {"queued", "running"}:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("Worker completion deadline exceeded")
        if current["status"] != "complete":
            raise RuntimeError("Full-stack discovery did not complete")
        specification = request(prefix + "/artifacts/openapi")
        operations = request(prefix + "/evidence/operations")
        if specification["openapi"] != "3.1.0" or not operations:
            raise RuntimeError("Full-stack artifacts are missing")
        first_identifier = next(
            (
                item["body"]["id"]
                for item in request(prefix + "/evidence/observations")
                if item["status"] == 201 and "id" in item["body"]
            ),
            None,
        )
        results.append(
            {
                "target": session["target"],
                "session": session["id"],
                "status": current["status"],
                "result": current["result"],
                "first_created_identifier": first_identifier,
            }
        )
    expected = {"ecommerce": 32, "subscriptions": 24, "warehouse": 32, "complex": 9}
    if any(item["result"]["operations"] != expected[item["target"]] for item in results):
        raise RuntimeError("Full-stack operation coverage regressed")
    if results[0]["result"] != results[-1]["result"] or any(
        item["first_created_identifier"] != 1 for item in results
    ):
        raise RuntimeError("Fixture session isolation failed")
    report = {
        "status": "passed",
        "session_isolation": "passed",
        "cancellation": "passed",
        "sessions": results,
    }
    Path("experiments/reports/stack-smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        "Full-stack smoke passed: four targets, repeated-session isolation, cancellation, artifacts."
    )


if __name__ == "__main__":
    main()
