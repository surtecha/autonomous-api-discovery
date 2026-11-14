"""Summarize independent benchmark suites without modifying source evidence."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from scripts.paths import workspace_path


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    for target in sorted({row["target"] for row in rows}):
        for strategy in sorted({row["strategy"] for row in rows}):
            samples = [r for r in rows if r["target"] == target and r["strategy"] == strategy]
            if not samples:
                continue
            metrics = {}
            for name in (
                "correct_operations",
                "endpoint_precision",
                "endpoint_recall",
                "requests",
                "request_field_type_accuracy",
                "required_field_accuracy",
                "response_schema_accuracy",
                "state_transition_coverage",
                "valid_request_rate",
                "requests_per_correct_operation",
                "unsupported_operations",
            ):
                values = [
                    r["evaluation"][name] for r in samples if r["evaluation"][name] is not None
                ]
                metrics[name] = (
                    {
                        "mean": statistics.mean(values),
                        "min": min(values),
                        "max": max(values),
                        "sample_stdev": statistics.stdev(values) if len(values) > 1 else None,
                    }
                    if values
                    else None
                )
            groups.append(
                {
                    "target": target,
                    "strategy": strategy,
                    "repetitions": len(samples),
                    "metrics": metrics,
                }
            )
    usage = {}
    for key in (
        "calls",
        "tokens",
        "input_tokens",
        "output_tokens",
        "failures",
        "parsed_selections",
        "unmeasured_calls",
        "latency_ms",
    ):
        usage[key] = sum(
            r["evaluation"]["model_usage"].get(key, 0) for r in rows if r["strategy"] == "llm"
        )
    return {
        "trials": len(rows),
        "groups": groups,
        "local_model_usage": usage,
        "sdk_tests": sum(r["validation"]["test_counts"]["tests"] for r in rows),
        "sdk_bundles_passed": sum(
            all(
                r["validation"].get(k) == "passed"
                for k in ("sdk_tests", "sdk_lint", "sdk_types", "sdk_packaging")
            )
            for r in rows
        ),
        "local_provider_api_fees_usd": 0,
        "hardware_electricity_cost_usd": None,
        "limitations": [
            "Four project-owned fixtures; no general enterprise API claim.",
            "Five repetitions; deterministic schedules are repeated controls.",
            "Three model calls per run, then gain fallback; model ranking only.",
            "Elapsed run time includes SDK validation and overlapping workloads; not a speed benchmark.",
            "Local API fees are zero; total operating cost was not metered.",
        ],
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--llm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for root in (args.baseline, args.llm):
        rows.extend(json.loads((workspace_path(root) / "summary.json").read_text()))
    expected = {
        (target, strategy, repetition)
        for target in ("ecommerce", "subscriptions", "warehouse", "complex")
        for strategy in ("fifo", "random", "gain", "llm")
        for repetition in range(5)
    }
    actual = [(r["target"], r["strategy"], r["repetition"]) for r in rows]
    if len(actual) != 80 or set(actual) != expected:
        raise ValueError("Expected exactly four fixtures, four strategies, and five repetitions")
    with workspace_path(args.output).open("x") as handle:
        handle.write(json.dumps(summarize(rows), indent=2) + "\n")


if __name__ == "__main__":
    main()
