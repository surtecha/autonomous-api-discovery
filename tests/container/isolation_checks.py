"""Executed only inside the networkless validator, never directly on the host."""

import os
import socket
from pathlib import Path

import pytest


def test_non_root():
    assert os.getuid() == 65532


def test_no_application_credentials():
    for name in (
        "OPENAI_API_KEY",
        "BACKEND_API_TOKEN",
        "DATABASE_URL",
        "GITHUB_TOKEN",
        "SSH_AUTH_SOCK",
    ):
        assert name not in os.environ
    assert not Path("/var/run/docker.sock").exists()
    try:
        assert not Path("/root/.ssh").exists()
    except PermissionError:
        pass  # The non-root validator cannot access the root user's directory.


def test_root_read_only():
    with pytest.raises(OSError):
        Path("/isolation-write-probe").write_text("synthetic")


def test_project_target_network_unreachable():
    with pytest.raises(OSError):
        socket.create_connection(("172.30.91.11", 9101), timeout=0.2)
