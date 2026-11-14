"""Hypothesis-driven exploration based solely on sanitized wire observations."""

from __future__ import annotations

import random
import re
from dataclasses import replace
from typing import Protocol

from .inference import infer, merge
from .models import Experiment, Json, Knowledge, Observation
from .security import PolicyError


class Executor(Protocol):
    def execute(self, experiment: Experiment) -> Observation: ...


def canonical(path: str) -> str:
    return re.sub(r"/\d+(?=/|$)", "/{id}", path.split("?")[0])


def enqueue(state: Knowledge, experiment: Experiment) -> None:
    if (
        len(state.pending) < 200
        and experiment.key not in state.seen
        and all(candidate.key != experiment.key for candidate in state.pending)
    ):
        state.pending.append(experiment)


def score(state: Knowledge, experiment: Experiment) -> float:
    operation = state.operations.get(experiment.method + " " + canonical(experiment.path))
    novelty = 1.0 if operation is None else 0.2
    verification = 1.5 if experiment.omitted else 0.0
    return (experiment.gain + novelty + verification) / max(1.0, experiment.cost)


def choose(state: Knowledge) -> Experiment:
    if state.strategy == "random":
        index = random.Random(len(state.seen) + state.random_seed).randrange(len(state.pending))
    elif state.strategy == "fifo":
        index = 0
    else:
        index = max(range(len(state.pending)), key=lambda i: score(state, state.pending[i]))
    return state.pending.pop(index)


def resource_path(path: str) -> str:
    parts = path.split("?")[0].strip("/").split("/")
    numeric = next((i for i, part in enumerate(parts) if part.isdigit()), None)
    return "/" + "/".join(parts[:numeric] if numeric is not None else parts)


def links(state: Knowledge, observation: Observation) -> None:
    advertised = observation.body.get("links", [])
    if not isinstance(advertised, list):
        return
    for link in advertised:
        if not isinstance(link, dict):
            continue
        method, path = link.get("method", "GET"), link.get("href")
        if (
            isinstance(method, str)
            and method in {"GET", "POST", "PATCH", "DELETE"}
            and isinstance(path, str)
            and path.startswith("/")
        ):
            enqueue(
                state,
                Experiment(
                    method,
                    path,
                    {} if method in {"POST", "PATCH"} else None,
                    safety="mutation" if method not in {"GET"} else "read",
                ),
            )
            if not re.search(r"/\d+", path) and "?" not in path:
                enqueue(
                    state,
                    Experiment(
                        "OPTIONS", path, gain=0.2, hypothesis="Inspect advertised HTTP methods"
                    ),
                )


def update_requirement(claim: Json, required: bool, evidence: str) -> None:
    conflict = claim.get("conflict", False) or (
        claim.get("verified", False) and claim.get("required") != required
    )
    claim.update(
        required=None if conflict else required,
        verified=not conflict,
        confidence=0.5 if conflict else 0.95,
        conflict=conflict,
    )
    if evidence not in claim["evidence"]:
        claim["evidence"].append(evidence)


def interpret(state: Knowledge, observation: Observation) -> None:
    state.observations.append(observation)
    if observation.category not in {"http", "in_process_fixture"}:
        state.rejected.append({"experiment": observation.id, "category": observation.category})
        return
    exp = observation.experiment
    key = exp.method + " " + canonical(exp.path)
    links(state, observation)
    if observation.status == 429:
        # Schedule at the end of the current queue, with a bounded retry count.
        if exp.retries < 3:
            enqueue(
                state,
                replace(exp, retries=exp.retries + 1, revision=len(state.observations), gain=0.1),
            )
        state.rejected.append(
            {"experiment": observation.id, "status": 429, "meaning": "Rate limited"}
        )
        return
    if 200 <= observation.status < 300:
        if exp.method in {"POST", "PATCH", "PUT"} and not exp.omitted:
            waiting, state.blocked = state.blocked, []
            for candidate in waiting:
                if candidate.retries < 3:
                    enqueue(
                        state,
                        replace(
                            candidate,
                            revision=len(state.observations),
                            retries=candidate.retries + 1,
                            gain=0.5,
                            parent=observation.id,
                        ),
                    )
        op = state.operations.setdefault(
            key,
            {
                "method": exp.method,
                "path": canonical(exp.path),
                "evidence": [],
                "request": {},
                "responses": {},
                "fields": {},
                "verified": True,
            },
        )
        op["evidence"].append(observation.id)
        for relationship in state.relationships:
            if relationship["operation"] == key and exp.body and relationship["field"] in exp.body:
                relationship["verified"] = True
                relationship["evidence"].append(observation.id)
        code = str(observation.status)
        op["responses"][code] = merge(op["responses"].get(code, {}), infer(observation.body))
        if exp.body is not None:
            op["request"] = merge(op["request"], infer(exp.body))
            for field in exp.body:
                claim = op["fields"].setdefault(
                    field,
                    {
                        "required": None,
                        "confidence": 0.5,
                        "verified": False,
                        "type_verified": False,
                        "evidence": [observation.id],
                    },
                )
                if observation.id not in claim["evidence"]:
                    claim["evidence"].append(observation.id)
                if not exp.omitted and not exp.perturbed:
                    invalid = dict(exp.body)
                    invalid[field] = [] if not isinstance(exp.body[field], list) else False
                    enqueue(
                        state,
                        Experiment(
                            exp.method,
                            exp.path,
                            invalid,
                            hypothesis="Perturb one field type",
                            gain=0.8,
                            safety="mutation",
                            parent=observation.id,
                            perturbed=field,
                        ),
                    )
                reduced = {k: v for k, v in exp.body.items() if k != field}
                enqueue(
                    state,
                    Experiment(
                        exp.method,
                        exp.path,
                        reduced,
                        hypothesis="Omission tests field necessity",
                        gain=1.2,
                        safety="mutation",
                        parent=observation.id,
                        omitted=field,
                    ),
                )
        identifier = observation.body.get("id")
        if isinstance(identifier, int):
            parts = exp.path.strip("/").split("/")
            numeric = next((i for i, part in enumerate(parts) if part.isdigit()), None)
            collection = parts[numeric - 1] if numeric is not None else parts[-1]
            state.resources.setdefault(collection, [])
            if identifier not in state.resources[collection]:
                state.resources[collection].append(identifier)
        status = observation.body.get("status")
        if status:
            previous = next(
                (
                    o
                    for o in reversed(state.observations[:-1])
                    if o.body.get("id") == identifier
                    and resource_path(o.experiment.path) == resource_path(exp.path)
                    and o.body.get("status")
                ),
                None,
            )
            action = bool(re.search(r"/\d+/[a-zA-Z_]+$", exp.path))
            if (
                previous
                and exp.method in {"POST", "PATCH", "PUT"}
                and (previous.body["status"] != status or action)
            ):
                transition = {
                    "operation": key,
                    "from": previous.body["status"],
                    "to": status,
                    "evidence": [previous.id, observation.id],
                    "verified": True,
                }
                if not any(
                    t["operation"] == key and t["from"] == transition["from"] and t["to"] == status
                    for t in state.transitions
                ):
                    state.transitions.append(transition)
        if exp.omitted and key in state.operations:
            omitted_claim = state.operations[key]["fields"].get(exp.omitted)
            if omitted_claim:
                update_requirement(omitted_claim, False, observation.id)
        return
    errors = observation.body.get("errors", [])
    if not isinstance(errors, list):
        return
    if any(
        isinstance(error, dict)
        and isinstance(error.get("code"), str)
        and error.get("code") in {"state", "range"}
        for error in errors
    ):
        if exp.retries < 3 and not exp.omitted:
            state.blocked.append(exp)
        if re.search(r"/\d+", exp.path):
            matched_resource = re.match(r"(.*/\d+)", exp.path)
            if matched_resource:
                enqueue(
                    state,
                    Experiment(
                        "GET",
                        matched_resource.group(1),
                        revision=len(state.observations),
                        hypothesis="Check resource state after failed mutation",
                    ),
                )
    repaired = dict(exp.body or {})
    changed = False
    for error in errors:
        if not isinstance(error, dict):
            continue
        field = error.get("field", "")
        code = error.get("code", "")
        if not isinstance(field, str) or field == "[redacted]" or not isinstance(code, str):
            continue
        if exp.perturbed == field and code == "type" and key in state.operations:
            claim = state.operations[key]["fields"].get(field)
            if claim and exp.parent in claim["evidence"]:
                claim["type_verified"] = True
                claim["evidence"].append(observation.id)
            continue
        if exp.omitted == field and code == "required" and key in state.operations:
            claim = state.operations[key]["fields"].get(field)
            if claim and exp.parent in claim["evidence"]:
                update_requirement(claim, True, observation.id)
            continue
        if code == "reference":
            resource = error.get("resource", "")
            if not isinstance(resource, str):
                continue
            ids = state.resources.get(resource, [])
            relationship = {
                "operation": key,
                "field": field,
                "resource": error.get("resource"),
                "evidence": [observation.id],
                "verified": False,
            }
            if not any(r["operation"] == key and r["field"] == field for r in state.relationships):
                state.relationships.append(relationship)
            if ids:
                repaired[field] = ids[-1]
                changed = True
            elif (
                exp.retries < 3
                and not exp.omitted
                and not exp.perturbed
                and all(candidate.key != exp.key for candidate in state.blocked)
            ):
                state.blocked.append(exp)
        elif code in {"required", "type", "range"}:
            field_type = error.get("type")
            if not isinstance(field_type, str):
                continue
            value = {
                "string": "probe",
                "integer": 1,
                "number": 1.0,
                "boolean": True,
                "object": {},
                "array": [],
            }.get(field_type, "probe")
            if repaired.get(field) != value:
                repaired[field] = value
                changed = True
    if changed and not exp.omitted and not exp.perturbed:
        enqueue(
            state,
            replace(
                exp,
                body=repaired,
                parent=observation.id,
                gain=2.0,
                hypothesis="Repair structured validation failure",
            ),
        )
    state.rejected.append(
        {
            "experiment": observation.id,
            "status": observation.status,
            "meaning": "Failure does not establish endpoint absence",
        }
    )


def step(state: Knowledge, gateway: Executor) -> Knowledge:
    if not state.pending:
        state.status = "complete"
        return state
    experiment = choose(state)
    state.seen.add(experiment.key)
    try:
        observation = gateway.execute(experiment)
    except PolicyError as error:
        state.rejected.append(
            {"experiment": experiment.key, "category": "policy", "reason": str(error)}
        )
        if "budget" in str(error).lower():
            state.status = "budget_exhausted"
        elif "Uncertain" in str(error):
            state.status = "interrupted"
        elif "cancelled" in str(error):
            state.status = "cancelled"
        return state
    interpret(state, observation)
    return state


def initialize(
    session_id: str, seeds: list[str] | None = None, strategy: str = "gain"
) -> Knowledge:
    state = Knowledge(session_id, strategy=strategy)
    for seed in seeds or ["/"]:
        enqueue(state, Experiment("GET", seed))
    return state
