"""Run an authorized local discovery session and generate evidence artifacts."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from packages.discovery.artifacts import generate
from packages.discovery.engine import initialize, step
from packages.discovery.gateway import Gateway
from packages.discovery.persistence import JournaledGateway, Store
from packages.discovery.security import TargetPolicy
from scripts.paths import workspace_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--session", default=None)
    parser.add_argument("--strategy", choices=["gain", "fifo", "random", "llm"], default="gain")
    parser.add_argument("--runner", choices=["graph", "core"], default="graph")
    args = parser.parse_args()
    args.config = workspace_path(args.config)
    args.output = workspace_path(args.output)
    policy = TargetPolicy(**json.loads(args.config.read_text()))
    policy.validate()
    session = args.session or str(uuid.uuid4())
    args.output.mkdir(parents=True, exist_ok=True)
    if args.runner == "graph":
        from packages.discovery.graph import run_graph

        state = run_graph(session, policy, args.output, args.strategy)
    else:
        store = Store(args.output / "evidence.sqlite")
        state = store.load(session) or initialize(session, strategy=args.strategy)
        store.save(state)
        used, started = store.budget(session)
        gateway = JournaledGateway(
            Gateway(policy, used=used, started=started, session_id=session), store, session
        )
        try:
            while state.status == "running":
                if store.cancelled(session):
                    state.status = "cancelled"
                    break
                step(state, gateway)
                store.save(state)
        finally:
            store.close()
    (args.output / "knowledge.json").write_text(json.dumps(state.to_dict(), indent=2) + "\n")
    validation = generate(state, args.output / "sdk")
    print(
        json.dumps(
            {
                "session": session,
                "status": state.status,
                "operations": len(state.operations),
                "requests": len(state.observations),
                "validation": validation,
            }
        )
    )


if __name__ == "__main__":
    main()
