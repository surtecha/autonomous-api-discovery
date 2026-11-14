"""Provider integration runs in a child process to avoid replacing global test providers."""

import os
import subprocess
import sys
import unittest


class TelemetryTests(unittest.TestCase):
    def test_console_exports_stages_without_exception_text(self):
        source = """
from packages.discovery.telemetry import configure, stage
from opentelemetry import metrics, trace
configure()
try:
    with stage('http_experiment', 'test-session'):
        raise RuntimeError('sensitive-body-must-never-export')
except RuntimeError:
    pass
metrics.get_meter_provider().force_flush()
trace.get_tracer_provider().force_flush()
metrics.get_meter_provider().shutdown()
trace.get_tracer_provider().shutdown()
"""
        result = subprocess.run(
            [sys.executable, "-c", source],
            env=os.environ | {"DISCOVERY_TELEMETRY": "console"},
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, "Telemetry exporter subprocess failed")
        self.assertIn("discovery.stage.executions", result.stdout)
        self.assertIn("http_experiment", result.stdout)
        self.assertIn("failure", result.stdout)
        self.assertNotIn("sensitive-body-must-never-export", result.stdout + result.stderr)
