"""Four disposable APIs with wire-visible affordances and hidden business rules."""

from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

# These definitions are available only to the target process and independent evaluator.
CATALOG: dict[str, dict[str, Any]] = {
    "ecommerce": {
        "customers": {"name": "string"},
        "products": {"name": "string", "quantity": "integer"},
        "orders": {"customer_id": "customers"},
        "items": {"order_id": "orders", "product_id": "products", "quantity": "integer"},
        "inventory": {"product_id": "products", "quantity": "integer"},
        "payments": {"order_id": "orders", "amount": "number"},
        "shipments": {"order_id": "orders"},
    },
    "subscriptions": {
        "accounts": {"name": "string"},
        "plans": {"name": "string", "amount": "number"},
        "subscriptions": {"account_id": "accounts", "plan_id": "plans"},
        "invoices": {"subscription_id": "subscriptions", "amount": "number"},
        "payments": {"invoice_id": "invoices", "amount": "number"},
    },
    "warehouse": {
        "warehouses": {"name": "string"},
        "locations": {"warehouse_id": "warehouses", "name": "string"},
        "stock": {"location_id": "locations", "quantity": "integer"},
        "transfers": {"stock_id": "stock", "location_id": "locations", "quantity": "integer"},
        "reservations": {"stock_id": "stock", "quantity": "integer"},
        "fulfillments": {"reservation_id": "reservations"},
        "returns": {"fulfillment_id": "fulfillments", "quantity": "integer"},
    },
    "complex": {
        "accounts": {"name": "string", "profile": "object"},
        "jobs": {"account_id": "accounts", "config": "object", "mode": "string"},
        "batches": {"job_id": "jobs", "entries": "array"},
    },
}
TRANSITIONS = {
    "ecommerce": {
        "orders": {
            "reserve": ("draft", "reserved"),
            "pay": ("reserved", "paid"),
            "ship": ("paid", "shipped"),
        }
    },
    "subscriptions": {
        "subscriptions": {
            "activate": ("draft", "active"),
            "renew": ("active", "active"),
            "cancel": ("active", "cancelled"),
        }
    },
    "warehouse": {
        "reservations": {"fulfill": ("draft", "fulfilled"), "return": ("fulfilled", "returned")}
    },
    "complex": {"jobs": {"validate": ("draft", "pending"), "complete": ("pending", "completed")}},
}


def link(method: str, path: str) -> dict[str, str]:
    return {"method": method, "href": path}


class Target:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.rules = CATALOG[kind]
        self.records: dict[str, dict[int, dict[str, Any]]] = {key: {} for key in self.rules}
        self.lock = threading.Lock()
        self.calls = 0

    def handle(self, method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        with self.lock:
            return self._handle(method, path, body)

    def _handle(self, method: str, path: str, body: Any) -> tuple[int, dict[str, Any]]:
        self.calls += 1
        prefix = "/v2" if self.kind == "complex" else ""
        parsed = urlsplit(path)
        if path == "/" and method == "GET":
            return 200, {
                "links": [link(m, prefix + "/" + r) for r in self.rules for m in ("GET", "POST")]
            }
        route = parsed.path
        if prefix:
            if not route.startswith(prefix + "/"):
                return 404, {"errors": [{"code": "not_found"}]}
            route = route[len(prefix) :]
        parts = route.strip("/").split("/")
        resource = parts[0]
        if resource not in self.rules:
            return 404, {"errors": [{"code": "not_found"}]}
        collection = prefix + "/" + resource
        if method == "OPTIONS" and len(parts) == 1:
            return 200, {"links": [link("GET", collection), link("POST", collection)]}
        if self.kind == "complex" and self.calls % 13 == 0:
            return 429, {"errors": [{"code": "rate_limit"}]}
        if len(parts) == 1 and method == "GET":
            query = parse_qs(parsed.query)
            try:
                cursor = int(query.get("cursor", ["0"])[0])
                limit = min(20, max(1, int(query.get("limit", ["2"])[0])))
            except ValueError:
                return 400, {"errors": [{"code": "type", "field": "cursor", "type": "integer"}]}
            items = list(self.records[resource].values())[cursor : cursor + limit]
            links = [link("POST", collection)]
            if cursor + limit < len(self.records[resource]):
                links.append(link("GET", collection + f"?cursor={cursor + limit}"))
            return 200, {"items": items, "total": len(self.records[resource]), "links": links}
        if len(parts) == 1 and method == "POST":
            if not isinstance(body, dict):
                return 400, {"errors": [{"code": "type", "field": "body", "type": "object"}]}
            errors = []
            for field, rule in self.rules[resource].items():
                expected = "integer" if rule in self.records else rule
                if field not in body:
                    errors.append({"field": field, "code": "required", "type": expected})
                    continue
                value = body[field]
                matches = {
                    "string": isinstance(value, str),
                    "integer": type(value) is int,
                    "number": type(value) in {int, float},
                    "object": isinstance(value, dict),
                    "array": isinstance(value, list),
                }
                if not matches.get(expected, False):
                    errors.append({"field": field, "code": "type", "type": expected})
                elif rule in self.records and value not in self.records[rule]:
                    errors.append(
                        {"field": field, "code": "reference", "resource": rule, "type": "integer"}
                    )
                elif expected in {"integer", "number"} and value <= 0:
                    errors.append({"field": field, "code": "range", "type": expected})
            if errors:
                return 422, {
                    "errors": errors,
                    "links": [
                        link("GET", prefix + "/" + e["resource"]) for e in errors if "resource" in e
                    ],
                }
            if (
                self.kind == "complex"
                and resource == "jobs"
                and ("region" not in body["config"] or body["mode"] not in {"batch", "stream"})
            ):
                return 400, {"message": "Configuration not accepted", "errors": []}
            if self.kind == "warehouse" and resource in {"transfers", "reservations"}:
                available = self.records["stock"][body["stock_id"]]["quantity"]
                if body["quantity"] > available:
                    return 409, {
                        "errors": [{"field": "quantity", "code": "range", "type": "integer"}],
                        "links": [
                            link("GET", f"/stock/{body['stock_id']}"),
                            link("PATCH", f"/stock/{body['stock_id']}"),
                        ],
                    }
            if (
                self.kind == "ecommerce"
                and resource == "shipments"
                and self.records["orders"][body["order_id"]]["status"] != "paid"
            ):
                return 409, {"errors": [{"code": "state"}]}
            if self.kind == "warehouse" and resource in {"transfers", "reservations"}:
                self.records["stock"][body["stock_id"]]["quantity"] -= body["quantity"]
            identifier = len(self.records[resource]) + 1
            record = {"id": identifier, **body, "status": "draft"}
            self.records[resource][identifier] = record
            return 201, {**record, "links": self._links(resource, identifier, prefix)}
        if len(parts) >= 2 and parts[1].isdigit():
            identifier = int(parts[1])
            record = self.records[resource].get(identifier)
            if record is None:
                return 404, {"errors": [{"code": "not_found"}]}
            if len(parts) == 2 and method == "GET":
                return 200, {**record, "links": self._links(resource, identifier, prefix)}
            if (
                self.kind == "warehouse"
                and resource == "stock"
                and len(parts) == 2
                and method == "PATCH"
            ):
                if not isinstance(body, dict) or "quantity" not in body:
                    return 422, {
                        "errors": [{"field": "quantity", "code": "required", "type": "integer"}]
                    }
                if type(body["quantity"]) is not int:
                    return 422, {
                        "errors": [{"field": "quantity", "code": "type", "type": "integer"}]
                    }
                if body["quantity"] < 1:
                    return 422, {
                        "errors": [{"field": "quantity", "code": "range", "type": "integer"}]
                    }
                record["quantity"] = body["quantity"]
                return 200, {**record, "links": self._links(resource, identifier, prefix)}
            transitions = TRANSITIONS[self.kind].get(resource, {})
            if len(parts) == 3 and parts[2] in transitions and method == "POST":
                before, after = transitions[parts[2]]
                if record["status"] != before:
                    return 409, {
                        "id": identifier,
                        "status": record["status"],
                        "errors": [{"code": "state"}],
                        "links": self._links(resource, identifier, prefix),
                    }
                if self.kind == "ecommerce" and resource == "orders":
                    if parts[2] == "reserve":
                        items = [
                            item
                            for item in self.records["items"].values()
                            if item["order_id"] == identifier
                        ]
                        if not items or any(
                            not any(
                                stock["product_id"] == item["product_id"]
                                and stock["quantity"] >= item["quantity"]
                                for stock in self.records["inventory"].values()
                            )
                            for item in items
                        ):
                            return 409, {
                                "id": identifier,
                                "status": record["status"],
                                "errors": [{"code": "state"}],
                                "links": [link("POST", "/items"), link("POST", "/inventory")],
                            }
                    if parts[2] == "pay" and not any(
                        payment["order_id"] == identifier
                        for payment in self.records["payments"].values()
                    ):
                        return 409, {
                            "id": identifier,
                            "status": record["status"],
                            "errors": [{"code": "state"}],
                            "links": [link("POST", "/payments")],
                        }
                    if parts[2] == "ship" and not any(
                        shipment["order_id"] == identifier
                        for shipment in self.records["shipments"].values()
                    ):
                        return 409, {
                            "id": identifier,
                            "status": record["status"],
                            "errors": [{"code": "state"}],
                            "links": [link("POST", "/shipments")],
                        }
                record["status"] = after
                return 200, {**record, "links": self._links(resource, identifier, prefix)}
        return 405, {"errors": [], "links": self._links(resource, 1, prefix)}

    def _links(self, resource: str, identifier: int, prefix: str) -> list[dict[str, str]]:
        path = f"{prefix}/{resource}/{identifier}"
        return [link("GET", path)] + [
            link("POST", path + "/" + action) for action in TRANSITIONS[self.kind].get(resource, {})
        ]


class TargetSessions:
    """Bounded disposable state per discovery session; no operator reset races."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.default = Target(kind)
        self.sessions: dict[str, tuple[float, Target]] = {}
        self.lock = threading.Lock()

    def get(self, session: str | None) -> Target:
        if session is None:
            return self.default
        session = str(uuid.UUID(session))
        now = time.monotonic()
        with self.lock:
            self.sessions = {
                key: value for key, value in self.sessions.items() if now - value[0] < 900
            }
            if session not in self.sessions:
                if len(self.sessions) >= 128:
                    raise ValueError("Fixture session capacity exceeded")
                self.sessions[session] = (now, Target(self.kind))
            target = self.sessions[session][1]
            self.sessions[session] = (now, target)
            return target


def serve(kind: str, port: int, host: str = "127.0.0.1") -> None:
    targets = TargetSessions(kind)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.dispatch()

        def do_POST(self) -> None:
            self.dispatch()

        def do_PATCH(self) -> None:
            self.dispatch()

        def do_OPTIONS(self) -> None:
            self.dispatch()

        def dispatch(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", 0))
                if not 0 <= length <= 8192:
                    self.send_error(413)
                    return
                body = json.loads(self.rfile.read(length)) if length else None
                target = targets.get(self.headers.get("X-Discovery-Session"))
                status, payload = target.handle(self.command, self.path, body)
            except (ValueError, UnicodeDecodeError):
                status, payload = 400, {"errors": []}
            raw = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: Any) -> None:
            return  # No raw paths, headers, or bodies in access logs.

    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=CATALOG)
    parser.add_argument("--port", type=int, default=9101)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    serve(args.kind, args.port, args.host)
