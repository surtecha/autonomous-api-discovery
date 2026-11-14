# Local v0.1 delivery record

Status: implementation complete for the local research release. The application is running on loopback; the reproducible release gate is `python -m scripts.verify`.

## Delivered behavior

The authenticated workspace creates bounded discovery sessions, shows persisted observations and field evidence, renders resource transitions and execution counts, and downloads generated artifacts. A PostgreSQL queue drives the LangGraph worker. Each dashboard session receives independent disposable target state. Cancellation and uncertain-request replay protection are implemented.

The discovery engine reconstructs only observed operations. It repairs supported structured errors, defers missing dependencies, verifies field requirements through controlled experiments, infers recursive response types, and records provenance. The SDK generator preserves wire names and supplies typed methods and bounded pagination helpers. Generated code executes only inside restricted validator containers during verification.

## Verified locally — 14 November 2026

| Release check | Result |
| --- | --- |
| Python suite, including PostgreSQL and Docker isolation | 67 passed, 0 skipped; 22 subtests passed |
| Live HTTP/TLS transport | Sanitization, malformed content, redirect/size rejection, valid SNI, and hostname mismatch tested over real sockets |
| Python Ruff and Mypy | Passed |
| Frontend ESLint, TypeScript, production build | Passed |
| Authenticated browser workflow | Passed, including downloads and reload persistence |
| Browser authentication and cross-origin write rejection | Passed |
| Desktop and mobile layout captures | Captured from the running application |
| All 12 fixture SDK bundles | Container tests, lint, strict typing, and packaging passed |
| Live generated-client workflows | Four targets; creation, pagination, errors, and supported workflows passed |
| Live HTTP evaluation | All 12 target/strategy combinations completed |
| OpenAPI standards and artifact consistency | Passed |
| Bandit at medium/high severity | No findings; four low-severity findings retained for review |
| Python and frontend dependency audits | No known dependency vulnerabilities found |
| Secret scanners | Gitleaks and detect-secrets pass on release inputs |
| Linux ARM64 application images | API, worker, targets, web, and validator built and exercised |

The complete machine-readable gate record is [release-checks.json](../experiments/reports/release-checks.json). Real HTTP results are in [http/summary.json](../experiments/reports/http/summary.json); fixture diagnostics remain explicitly labeled in-process. No hosted LLM call, provider bill, GitHub Actions run, or public deployment is represented by these local checks.

## Resolved delivery defects

- Rejected successful responses no longer crash SDK fixture generation.
- Missing dependency identifiers defer and retry after prerequisite resources exist; warehouse gain discovery now covers all 32 fixture operations.
- Independent benchmark processes use available loopback ports instead of colliding with existing services.
- Compose temporary filesystem options are correctly quoted.
- API and web ingress permits loopback publication while worker/target networks stay internal.
- Web CSRF checks use the configured public origin across port mappings.
- Non-root isolation checks handle inaccessible root directories.
- Docker restart policies recover services after process failures.
- Dashboard fixture namespaces prevent state leaking between discovery sessions.
- Pagination, live generated-client workflows, structural response-type scoring, opt-in telemetry export, private credential setup, and a reproducible release command are implemented.

## Deliberate research and deployment boundaries

The complex fixture withholds usable repair evidence for nested job configuration. The engine reports 9 of 15 operations and no job transitions rather than inventing a successful contract. General hidden conditional-input synthesis, arbitrary string identifiers, complete format/enum inference, and arbitrary authentication discovery are outside the supported inference grammar.

This release is a single-operator local system with a PostgreSQL control plane and SQLite evidence journals. Distributed artifact storage, fully normalized PostgreSQL evidence, enterprise identity/tenant isolation, and a hosted model egress deployment are separate extensions. Python dependency snapshots pin versions without artifact hashes. The measured fixture domain is intentionally smaller than a general enterprise API estate.

GitHub publication is a separate external action. Local completion does not claim a public repository, deployed hosted service, or remote CI execution.

## Local model extension — 15 November 2026

Verified local Qwen2.5 7B structured-output ranking via Ollama after hosted access returned HTTP 429 / `insufficient_quota`. Completed 80 fresh-process trials (four fixtures, four strategies, five repetitions), 60/60 parsed local selections, and 4,914 passing generated-SDK container tests across 80 bundles. Local-model assistance matched gain and FIFO; no superiority over either is claimed. Python regression: 73 passed, zero skips, 28 subtests. Earlier reports were preserved. Full results, usage, limitations, costs and resume metrics: [local-model results](../experiments/reports/local-model-20261115/results.md). This extension does not represent a rerun of the entire release gate.
