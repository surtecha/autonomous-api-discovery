"""Real loopback HTTP and TLS checks complement the deterministic socket mocks."""

import json
import ssl
import subprocess
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from test_core import policy
from test_support import temporary_directory

from packages.discovery.gateway import Gateway
from packages.discovery.models import Experiment
from packages.discovery.security import PolicyError, TargetPolicy


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = 302 if self.path == "/redirect" else 200
        content_type = "text/html" if self.path == "/html" else "application/json"
        raw = (
            b"not-json"
            if self.path == "/invalid"
            else json.dumps(
                {
                    "id": 1,
                    "message": "arbitrary response text",
                    "password": 42,
                }
            ).encode()
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        if status == 302:
            self.send_header("Location", "https://unrelated.invalid/")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@contextmanager
def server(context=None):
    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    if context is not None:
        instance.socket = context.wrap_socket(instance.socket, server_side=True)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance.server_address[1]
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=2)


class LiveTransportTests(unittest.TestCase):
    def test_live_http_sanitization_redirects_and_malformed_content(self):
        with server() as port:
            gateway = Gateway(policy(origin=f"http://127.0.0.1:{port}"))
            observed = gateway.execute(Experiment("GET", "/"))
            self.assertEqual(observed.body, {"id": 1, "message": "[redacted]"})
            self.assertEqual(
                gateway.execute(Experiment("GET", "/html")).category, "unsupported_content"
            )
            self.assertEqual(
                gateway.execute(Experiment("GET", "/invalid")).category, "malformed_json"
            )
            with self.assertRaisesRegex(PolicyError, "redirects"):
                gateway.execute(Experiment("GET", "/redirect"))
            with self.assertRaisesRegex(PolicyError, "size"):
                Gateway(policy(origin=f"http://127.0.0.1:{port}", max_response_bytes=8)).execute(
                    Experiment("GET", "/")
                )

    def test_live_tls_verifies_the_original_hostname(self):
        with temporary_directory() as folder:
            certificate, key = Path(folder) / "certificate.pem", Path(folder) / "private.key"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "1",
                    "-keyout",
                    str(key),
                    "-out",
                    str(certificate),
                    "-subj",
                    "/CN=fixture.test",
                    "-addext",
                    "subjectAltName=DNS:fixture.test",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=15,
            )
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certificate, key)
            trusted = ssl.create_default_context(cafile=str(certificate))
            with (
                server(context) as port,
                patch.object(TargetPolicy, "resolve", return_value="127.0.0.1"),
                patch(
                    "packages.discovery.gateway.ssl.create_default_context", return_value=trusted
                ),
            ):
                accepted = Gateway(policy(origin=f"https://fixture.test:{port}")).execute(
                    Experiment("GET", "/")
                )
                self.assertEqual(accepted.status, 200)
                rejected = Gateway(policy(origin=f"https://wrong.test:{port}")).execute(
                    Experiment("GET", "/")
                )
                self.assertEqual(rejected.category, "transport_error")
                self.assertEqual(rejected.body, {})
