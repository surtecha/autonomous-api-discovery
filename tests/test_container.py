import os
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(
    os.environ.get("RUN_SANDBOX_TESTS") == "1" and shutil.which("docker"),
    "Explicit sandbox execution and Docker validator image are required",
)
class ContainerIsolationTests(unittest.TestCase):
    def test_restricted_container(self):
        command = [
            "docker",
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--user=65532:65532",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory=256m",
            "--cpus=1",
            "--pids-limit=64",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "--env=HOME=/tmp",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--mount",
            f"type=bind,src={Path('tests/container').resolve()},dst=/checks,readonly",
            "api-discovery-validator:local",
            "python",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            "/checks/isolation_checks.py",
        ]
        result = subprocess.run(command, capture_output=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, "Container isolation checks failed")
