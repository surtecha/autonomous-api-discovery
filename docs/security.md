# Security verification

Run the following inside the dedicated environment after dependencies are available:

```bash
conda run -n api-discovery-ai python -m pytest tests/test_core.py tests/test_extended.py -q
conda run -n api-discovery-ai bandit -r packages apps/api -ll
conda run -n api-discovery-ai pip-audit
conda run -n api-discovery-ai python -m scripts.scan_secrets
gitleaks git --redact
conda run -n api-discovery-ai python scripts/security_scan.py
```

The current core suite exercises metadata rejection, unauthorized paths, origin credentials, remote mutation rejection, mixed DNS results, pinned connections, redirects, body limits, request budgets, duration budgets, response redaction, and text injection in several response fields.

Tests using mocked sockets verify policy and request construction. They do not establish container egress isolation. The sandbox validator must be run separately after Docker is available. Repository history scanning requires a real Git repository.

Never publish while any scanner reports an unresolved suspected credential. Findings contain filenames and categories, not matching secret values. Credentials must be rotated if exposure is verified. Removing a file from the latest tree does not remove history exposure.

The release scanner exports every tracked and untracked publishable Git input to a temporary directory and runs detect-secrets plus Gitleaks there. Private ignored runtime files are excluded by Git; an accidentally staged ignored file is included and scanned. Symlinks require review. Reports contain filenames, line numbers, and categories only. The detector disables remote secret verification. The full local gate also runs dependency advisory scans; these query package names and versions.
