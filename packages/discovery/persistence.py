"""Durable write-ahead attempt journal. Uncertain mutations are never replayed."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from .models import Experiment, Knowledge, Observation
from .security import PolicyError


class Store:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, state TEXT NOT NULL, started REAL NOT NULL,
                cancelled INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS attempts (
                session_id TEXT NOT NULL REFERENCES sessions(id), experiment_id TEXT NOT NULL,
                observation TEXT, PRIMARY KEY(session_id, experiment_id)
            );
        """)
        self.db.execute("PRAGMA foreign_keys=ON")

    def save(self, state: Knowledge) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO sessions(id,state,started) VALUES(?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state",
                (state.session_id, json.dumps(state.to_dict()), time.time()),
            )

    def load(self, session: str) -> Knowledge | None:
        row = self.db.execute("SELECT state FROM sessions WHERE id=?", (session,)).fetchone()
        return Knowledge.from_dict(json.loads(row[0])) if row else None

    def cancel(self, session: str) -> None:
        with self.db:
            self.db.execute("UPDATE sessions SET cancelled=1 WHERE id=?", (session,))

    def cancelled(self, session: str) -> bool:
        row = self.db.execute("SELECT cancelled FROM sessions WHERE id=?", (session,)).fetchone()
        return bool(row and row[0])

    def budget(self, session: str) -> tuple[int, float]:
        used = self.db.execute(
            "SELECT count(*) FROM attempts WHERE session_id=?", (session,)
        ).fetchone()[0]
        started = self.db.execute("SELECT started FROM sessions WHERE id=?", (session,)).fetchone()[
            0
        ]
        return used, started

    def close(self) -> None:
        self.db.close()


class JournaledGateway:
    def __init__(self, gateway: Any, store: Store, session: str) -> None:
        self.gateway, self.store, self.session = gateway, store, session

    def execute(self, experiment: Experiment) -> Observation:
        if self.store.cancelled(self.session):
            raise PolicyError("Session cancelled")
        cached = self.store.db.execute(
            "SELECT observation FROM attempts WHERE session_id=? AND experiment_id=?",
            (self.session, experiment.key),
        ).fetchone()
        if cached:
            if cached[0] is None:
                raise PolicyError(
                    "Uncertain interrupted attempt requires target reset and new session"
                )
            item = json.loads(cached[0])
            item["experiment"] = Experiment(**item["experiment"])
            return Observation(**item)
        with self.store.db:
            self.store.db.execute(
                "INSERT INTO attempts(session_id,experiment_id) VALUES(?,?)",
                (self.session, experiment.key),
            )
        observation = self.gateway.execute(experiment)
        with self.store.db:
            self.store.db.execute(
                "UPDATE attempts SET observation=? WHERE session_id=? AND experiment_id=?",
                (json.dumps(observation.to_dict()), self.session, experiment.key),
            )
        return observation
