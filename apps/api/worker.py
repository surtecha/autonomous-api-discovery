"""Single worker with PostgreSQL job claiming and crash-visible session status."""

from __future__ import annotations

import json
import logging
import shutil
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from packages.discovery.artifacts import generate
from packages.discovery.graph import run_graph
from packages.discovery.security import TargetPolicy

from .database import AuditEvent, DiscoverySession, database
from .settings import Settings


def main() -> None:
    from packages.discovery.telemetry import configure

    configure()
    settings = Settings()
    _, sessions = database(settings.database_url.get_secret_value())
    policies = {
        name: TargetPolicy(**value)
        for name, value in json.loads(settings.policy_file.read_text()).items()
    }
    owner = str(uuid.uuid4())
    while True:
        with sessions.begin() as db:
            # Expired jobs need explicit operator reconciliation. Never replay uncertain mutations.
            expired = db.scalars(
                select(DiscoverySession).where(
                    DiscoverySession.status == "running",
                    DiscoverySession.lease_until < datetime.now(UTC),
                )
            )
            for item in expired:
                item.status = "interrupted"
            job = db.scalar(
                select(DiscoverySession)
                .where(DiscoverySession.status == "queued")
                .order_by(DiscoverySession.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is not None:
                job.status = "running"
                job.owner = owner
                job.lease_until = datetime.now(UTC) + timedelta(minutes=12)
                session_id, target, budget, strategy = job.id, job.target, job.budget, job.strategy
        if job is None:
            time.sleep(1)
            continue
        directory = settings.artifact_root / session_id
        directory.mkdir(parents=True, exist_ok=True)
        status = "failed"
        result: dict[str, Any] = {"category": "worker_error"}
        try:
            state = run_graph(
                session_id, replace(policies[target], max_requests=budget), directory, strategy
            )
            (directory / "knowledge.json").write_text(json.dumps(state.to_dict(), indent=2))
            validation = generate(state, directory / "sdk")
            shutil.make_archive(str(directory / "sdk"), "zip", directory / "sdk")
            status = state.status
            result = {
                "operations": len(state.operations),
                "requests": len(state.observations),
                "transitions": len(state.transitions),
                "validation": validation,
            }
        except Exception:  # noqa: BLE001 - Job boundary records a sanitized failure and continues.
            logging.getLogger("discovery.worker").error(
                json.dumps(
                    {"stage": "worker", "session_id": session_id, "category": "execution_error"}
                )
            )
        with sessions.begin() as db:
            current = db.get(DiscoverySession, session_id, with_for_update=True)
            if current is not None and current.owner == owner and current.status == "running":
                current.status, current.result = status, result
                db.add(AuditEvent(session_id=session_id, category=status, payload=result))


if __name__ == "__main__":
    main()
