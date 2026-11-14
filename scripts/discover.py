"""Run an authorized local discovery session and generate evidence artifacts."""

from __future__ import annotations

import argparse
import json
import os
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
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--llm-provider", choices=["openai", "ollama"])
    parser.add_argument("--llm-model")
    parser.add_argument("--env-file", type=Path, help="Load provider settings from a private file")
    args = parser.parse_args()
    if args.strategy == "llm":
        if args.runner != "graph":
            parser.error("--strategy llm requires --runner graph")
        if args.env_file:
            if not args.env_file.is_file():
                parser.error("--env-file must name an existing private configuration file")
            from dotenv import dotenv_values

            for name, value in dotenv_values(args.env_file).items():
                if name in {"LLM_PROVIDER", "LLM_MODEL", "OPENAI_API_KEY"} and value is not None:
                    os.environ.setdefault(name, value)
        if args.llm_provider:
            os.environ["LLM_PROVIDER"] = args.llm_provider
        if args.llm_model:
            os.environ["LLM_MODEL"] = args.llm_model
        from packages.discovery.model_config import ModelConfig

        try:
            ModelConfig.from_environment()
        except ValueError as error:
            parser.error(str(error))
    args.config = workspace_path(args.config)
    args.output = workspace_path(args.output)
    policy = TargetPolicy(**json.loads(args.config.read_text()))
    policy.validate()
    session = args.session or str(uuid.uuid4())
    args.output.mkdir(parents=True, exist_ok=True)
    if args.runner == "graph":
        from packages.discovery.graph import run_graph

        state = run_graph(session, policy, args.output, args.strategy, args.seed)
    else:
        store = Store(args.output / "evidence.sqlite")
        state = store.load(session) or initialize(session, strategy=args.strategy)
        state.random_seed = args.seed
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
                **({"model_usage": state.model_usage} if args.strategy == "llm" else {}),
            }
        )
    )


if __name__ == "__main__":
    main()
