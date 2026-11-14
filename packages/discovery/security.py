"""Fail-closed origin policy and structural observation minimization."""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit


class PolicyError(ValueError):
    """An operation exceeded its explicitly granted capability."""


@dataclass(frozen=True)
class TargetPolicy:
    origin: str
    pinned_ips: tuple[str, ...]
    disposable: bool = False
    authorization: str = ""
    max_requests: int = 100
    duration_seconds: float = 120
    timeout_seconds: float = 3
    max_body_bytes: int = 8192
    max_response_bytes: int = 65536
    requests_per_second: float = 20
    fixture_sessions: bool = False

    def validate(self) -> None:
        if self.fixture_sessions and not self.disposable:
            raise PolicyError("Fixture sessions require a disposable target")
        if any(ord(char) < 33 or char in "\\%" for char in self.origin):
            raise PolicyError("Invalid origin encoding")
        parsed = urlsplit(self.origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise PolicyError("Unsupported origin")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise PolicyError("Origin contains prohibited components")
        if parsed.path not in {"", "/"} or parsed.port is None:
            raise PolicyError("An explicit origin port and empty path are required")
        if not self.authorization or not self.pinned_ips:
            raise PolicyError("Documented authorization and pinned addresses are required")
        if not 1 <= self.max_requests <= 1000 or not 0 < self.duration_seconds <= 600:
            raise PolicyError("Invalid session budget")
        if not 0 < self.timeout_seconds <= 10 or not 0 < self.requests_per_second <= 50:
            raise PolicyError("Invalid transport limits")
        if not 1 <= self.max_body_bytes <= 65536 or not 1 <= self.max_response_bytes <= 1048576:
            raise PolicyError("Invalid size limits")
        for address in self.pinned_ips:
            ip = ipaddress.ip_address(address)
            if isinstance(ip, ipaddress.IPv6Address) and (
                ip.ipv4_mapped or ip.sixtofour or ip.teredo
            ):
                raise PolicyError("IPv6 transition addresses are prohibited")
            if ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved:
                raise PolicyError("Prohibited address range")
            if not self.disposable and not ip.is_global:
                raise PolicyError("Remote policies require public addresses")
            if self.disposable and not (ip.is_loopback or ip.is_private):
                raise PolicyError("Disposable targets must be local")

    def resolve(self) -> str:
        self.validate()
        parsed = urlsplit(self.origin)
        answers = {
            str(item[4][0])
            for item in socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
        }
        if not answers or not answers.issubset(set(self.pinned_ips)):
            raise PolicyError("DNS addresses differ from authorized pins")
        return min(answers)

    def validate_request(self, method: str, path: str) -> None:
        self.validate()
        if method not in {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"}:
            raise PolicyError("Unsupported method")
        if method not in {"GET", "HEAD", "OPTIONS"} and not self.disposable:
            raise PolicyError("Remote mutation is disabled")
        if not re.fullmatch(r"/[A-Za-z0-9_/-]*(?:\?(?:limit|cursor)=[0-9]{1,6})?", path):
            raise PolicyError("Path is outside the bounded request grammar")
        if "//" in path or any(
            part in {"admin", "reset", "debug", "metrics"} for part in path.split("?")[0].split("/")
        ):
            raise PolicyError("Reserved control path")


def sanitize(value: Any, *, key: str = "", depth: int = 0) -> Any:
    """Retain structure and narrowly typed control values, never arbitrary text."""
    if depth > 12:
        return None
    if isinstance(value, dict):
        result = {}
        for name, item in list(value.items())[:100]:
            if not re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]{0,63}", name):
                continue
            if any(
                word in name.lower()
                for word in (
                    "token",
                    "secret",
                    "password",
                    "cookie",
                    "authorization",
                    "email",
                    "key",
                )
            ):
                continue
            result[name] = sanitize(item, key=name, depth=depth + 1)
        return result
    if isinstance(value, list):
        return [sanitize(item, key=key, depth=depth + 1) for item in value[:50]]
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return (
            value
            if key in {"id", "cursor", "limit", "quantity", "total"} or key.endswith("_id")
            else (0.0 if isinstance(value, float) else 0)
        )
    if isinstance(value, str):
        patterns = {
            "href": r"/[a-zA-Z0-9_/-]{0,180}(?:\?(?:limit|cursor)=[0-9]{1,6})?",
            "method": r"GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
            "field": r"[a-z][a-z_0-9]{0,40}",
            "resource": r"[a-z][a-z_0-9]{0,40}",
            "type": r"string|integer|number|boolean|object|array",
            "code": r"required|type|reference|state|enum|range|not_found|rate_limit",
            "status": r"draft|created|active|cancelled|paid|shipped|reserved|fulfilled|returned|completed|pending",
        }
        if key in patterns and re.fullmatch(patterns[key], value):
            return value
        return "[redacted]"
    return None
