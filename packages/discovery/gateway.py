"""Single-flight HTTP gateway with pinned sockets and no redirect following."""

from __future__ import annotations

import http.client
import json
import socket
import ssl
import threading
import time
import uuid
from collections.abc import Callable
from urllib.parse import urlsplit

from .models import Experiment, Observation
from .security import PolicyError, TargetPolicy, sanitize


class Gateway:
    def __init__(
        self,
        policy: TargetPolicy,
        credential: Callable[[], str | None] | None = None,
        used: int = 0,
        started: float | None = None,
        session_id: str | None = None,
    ) -> None:
        policy.validate()
        self.policy = policy
        self.credential = credential
        self.fixture_session = (
            str(uuid.UUID(session_id)) if policy.fixture_sessions and session_id else None
        )
        self.used = used
        self.started = started if started is not None else time.time()
        self.last_request = 0.0
        self.lock = threading.Lock()

    def execute(self, experiment: Experiment) -> Observation:
        with self.lock:
            return self._execute(experiment)

    def _execute(self, experiment: Experiment) -> Observation:
        policy = self.policy
        policy.validate_request(experiment.method, experiment.path)
        payload = (
            json.dumps(experiment.body, allow_nan=False).encode()
            if experiment.body is not None
            else None
        )
        if payload and len(payload) > policy.max_body_bytes:
            raise PolicyError("Request body limit exceeded")
        if (
            self.used >= policy.max_requests
            or time.time() - self.started >= policy.duration_seconds
        ):
            raise PolicyError("Session budget exhausted")
        try:
            address = policy.resolve()
        except OSError:
            self.used += 1
            return Observation(experiment.key, experiment, 0, {}, 0.0, "dns_error")
        delay = max(0.0, 1 / policy.requests_per_second - (time.monotonic() - self.last_request))
        if time.time() - self.started + delay >= policy.duration_seconds:
            raise PolicyError("Session budget exhausted")
        time.sleep(delay)
        self.used += 1  # Failed requests consume budget too.
        self.last_request = time.monotonic()
        begin = time.monotonic()
        parsed = urlsplit(policy.origin)
        timeout = min(
            policy.timeout_seconds, policy.duration_seconds - (time.time() - self.started)
        )
        if timeout <= 0:
            raise PolicyError("Session budget exhausted")
        connection = http.client.HTTPConnection(address, parsed.port, timeout=timeout)
        headers = {
            "Host": parsed.netloc,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.fixture_session:
            headers["X-Discovery-Session"] = self.fixture_session
        if self.credential:
            token = self.credential()
            if token:
                if "\r" in token or "\n" in token:
                    raise PolicyError("Invalid credential format")
                headers["Authorization"] = "Bearer " + token
        timer: threading.Timer | None = None
        try:
            # Connect only to the approved numeric address. TLS uses the original hostname.
            connection.connect()
            if parsed.scheme == "https":
                assert connection.sock is not None
                connection.sock = ssl.create_default_context().wrap_socket(
                    connection.sock, server_hostname=parsed.hostname
                )

            def abort() -> None:
                if connection.sock is not None:
                    try:
                        connection.sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    connection.close()

            remaining = timeout - (time.monotonic() - begin)
            if remaining <= 0:
                raise TimeoutError("Request deadline expired")
            timer = threading.Timer(remaining, abort)
            timer.daemon = True
            timer.start()
            connection.request(experiment.method, experiment.path, payload, headers)
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise PolicyError("All redirects are rejected")
            content_type = response.getheader("Content-Type", "").split(";")[0].strip()
            if content_type != "application/json":
                return Observation(
                    experiment.key,
                    experiment,
                    response.status,
                    {},
                    (time.monotonic() - begin) * 1000,
                    "unsupported_content",
                )
            raw = response.read(policy.max_response_bytes + 1)
            if len(raw) > policy.max_response_bytes:
                raise PolicyError("Response size limit exceeded")
            try:
                data = json.loads(raw, parse_constant=lambda value: None)
            except (ValueError, UnicodeDecodeError, RecursionError):
                return Observation(
                    experiment.key,
                    experiment,
                    response.status,
                    {},
                    (time.monotonic() - begin) * 1000,
                    "malformed_json",
                )
            clean = sanitize(data)
            return Observation(
                experiment.key,
                experiment,
                response.status,
                clean if isinstance(clean, dict) else {"items": clean},
                (time.monotonic() - begin) * 1000,
            )
        except (TimeoutError, OSError, http.client.HTTPException):
            return Observation(
                experiment.key,
                experiment,
                0,
                {},
                (time.monotonic() - begin) * 1000,
                "transport_error",
            )
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
