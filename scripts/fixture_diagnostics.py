"""In-process development diagnostics. Not an independent black-box HTTP benchmark."""

from __future__ import annotations

import json
import time
from pathlib import Path

from packages.discovery.artifacts import generate
from packages.discovery.engine import initialize, step
from packages.discovery.evaluation import evaluate
from packages.discovery.models import Experiment, Observation
from packages.discovery.security import sanitize
from targets.service import Target


class FixtureAdapter:
    def __init__(self, kind: str) -> None:
        self.target = Target(kind)

    def execute(self, experiment: Experiment) -> Observation:
        begin = time.monotonic()
        status, payload = self.target.handle(experiment.method, experiment.path, experiment.body)
        return Observation(
            experiment.key,
            experiment,
            status,
            sanitize(payload),
            (time.monotonic() - begin) * 1000,
            "in_process_fixture",
        )


def main() -> None:
    output = Path("experiments/reports/fixture-diagnostics")
    summary = []
    for kind in ("ecommerce", "subscriptions", "warehouse", "complex"):
        for strategy in ("fifo", "random", "gain"):
            state = initialize(f"fixture-{kind}-{strategy}", strategy=strategy)
            adapter = FixtureAdapter(kind)
            for _ in range(100):
                if state.status != "running":
                    break
                step(state, adapter)
            if state.status == "running":
                state.status = "budget_exhausted"
            directory = output / kind / strategy
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "knowledge.json").write_text(json.dumps(state.to_dict(), indent=2) + "\n")
            validation = generate(state, directory / "sdk")
            truth = json.loads(Path(f"targets/ground_truth/{kind}.json").read_text())
            metrics = evaluate(state, truth)
            metrics.update(
                {
                    "transport": "in_process_fixture",
                    "independent_black_box_benchmark": False,
                    "gateway_exercised": False,
                    "validation": validation,
                }
            )
            (directory / "diagnostics.json").write_text(json.dumps(metrics, indent=2) + "\n")
            summary.append({"target": kind, **metrics})
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            [
                {
                    key: row[key]
                    for key in (
                        "target",
                        "strategy",
                        "correct_operations",
                        "requests",
                        "endpoint_precision",
                        "endpoint_recall",
                        "required_field_accuracy",
                        "state_transition_coverage",
                    )
                }
                for row in summary
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
