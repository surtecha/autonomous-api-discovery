"""Dependency-free domain contracts shared by deterministic and graph runners."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

Json = dict[str, Any]


@dataclass(frozen=True)
class Experiment:
    method: str
    path: str
    body: Json | None = None
    hypothesis: str = "Inspect an advertised operation"
    expected: str = "Distinguish success, validation, and missing prerequisites"
    gain: float = 1.0
    cost: float = 1.0
    safety: str = "read"
    parent: str | None = None
    omitted: str | None = None
    perturbed: str | None = None
    revision: int = 0
    retries: int = 0

    @property
    def key(self) -> str:
        payload = json.dumps(
            [self.method, self.path, self.body, self.omitted, self.perturbed, self.revision],
            sort_keys=True,
        )
        return "exp_" + sha256(payload.encode()).hexdigest()[:24]


@dataclass
class Observation:
    id: str
    experiment: Experiment
    status: int
    body: Json
    elapsed_ms: float
    category: str = "http"

    def to_dict(self) -> Json:
        return asdict(self)


@dataclass
class Knowledge:
    session_id: str
    pending: list[Experiment] = field(default_factory=list)
    blocked: list[Experiment] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)
    operations: Json = field(default_factory=dict)
    resources: dict[str, list[int]] = field(default_factory=dict)
    transitions: list[Json] = field(default_factory=list)
    model_usage: Json = field(
        default_factory=lambda: {
            "calls": 0,
            "tokens": 0,
            "failures": 0,
            "latency_ms": 0.0,
            "budget_tokens": 0,
            "unmeasured_calls": 0,
        }
    )
    relationships: list[Json] = field(default_factory=list)
    rejected: list[Json] = field(default_factory=list)
    status: str = "running"
    strategy: str = "gain"

    def to_dict(self) -> Json:
        value = asdict(self)
        value["seen"] = sorted(self.seen)
        return value

    @classmethod
    def from_dict(cls, value: Json) -> Knowledge:
        state = cls(value["session_id"], strategy=value.get("strategy", "gain"))
        state.pending = [Experiment(**item) for item in value["pending"]]
        state.blocked = [Experiment(**item) for item in value.get("blocked", [])]
        for item in value["observations"]:
            item = dict(item)
            item["experiment"] = Experiment(**item["experiment"])
            state.observations.append(Observation(**item))
        for name in (
            "operations",
            "resources",
            "transitions",
            "rejected",
            "status",
            "model_usage",
            "relationships",
        ):
            setattr(state, name, value.get(name, getattr(state, name)))
        state.seen = set(value["seen"])
        return state
