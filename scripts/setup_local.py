"""Create private, disposable local credentials without printing their values."""

from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=3000)
    args = parser.parse_args()
    if not all(1024 <= port <= 65535 for port in (args.api_port, args.web_port)):
        parser.error("Ports must be between 1024 and 65535")
    path = Path(".env")
    values = {
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "BACKEND_API_TOKEN": secrets.token_hex(32),
        "WEB_USERNAME": "operator",
        "WEB_PASSWORD": secrets.token_hex(24),
        "API_PORT": str(args.api_port),
        "WEB_PORT": str(args.web_port),
        "WEB_ORIGIN": f"http://127.0.0.1:{args.web_port}",
        "DISCOVERY_TELEMETRY": "off",
    }
    # Exclusive creation preserves an operator's existing credentials and configuration.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as file:
        file.write("".join(f"{name}={value}\n" for name, value in values.items()))
    print("Created private .env. Use WEB_USERNAME and WEB_PASSWORD from that file to sign in.")


if __name__ == "__main__":
    main()
