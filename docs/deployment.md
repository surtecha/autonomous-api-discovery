# Deployment

## Prerequisites

Python 3.12 in Conda environment `api-discovery-ai`, Node.js 24 or later, npm, Docker with Compose, and Git are required for the full local workflow. GitHub CLI is optional for a separate publication task.

```bash
conda create -n api-discovery-ai python=3.12 -y
bash scripts/bootstrap.sh
```

The bootstrap script verifies interpreter isolation and installs exact dependency snapshots using pip with `--no-user`. It uses `npm ci` for the frontend. `python -m scripts.lock_dependencies` can regenerate Python snapshots after an intentional dependency update. Python snapshots contain exact versions but no artifact hashes. Linux ARM64 images and dependency advisory checks have passed locally.

## Runtime configuration

Run `python -m scripts.setup_local` to generate a private, ignored `.env`, or configure `.env.example` manually. The setup command never overwrites an existing file. For occupied ports use `--api-port 18000 --web-port 13000`. Set `POSTGRES_PASSWORD`, `BACKEND_API_TOKEN` with at least 32 characters, `WEB_USERNAME`, and `WEB_PASSWORD` with at least 16 characters. Never copy hosted credentials into reports or commands captured in shared logs.

The Compose database URL is assembled server-side with SQLAlchemy URL encoding from the runtime password. For a host API process, configure `DATABASE_URL` with the `postgresql+psycopg` scheme. Configuration errors fail startup. No anonymous non-local backend mode exists.

```bash
docker compose up --build -d
```

The migration service runs before the API and worker. The web interface is available on `http://127.0.0.1:3000`, protected by HTTP Basic authentication. The backend is on `http://127.0.0.1:8000` and requires the runtime bearer token.

Targets have fixed private addresses on an internal Docker network. API and web additionally join an ingress bridge so loopback port publication works on Docker Desktop. The worker remains on internal networks. `API_PORT` and `WEB_PORT` configure published ports; Compose derives the web CSRF origin from `WEB_PORT`. For a host web process, set `WEB_ORIGIN` to its exact public origin. Only the API and web ports are published, both on loopback. Containers have no Docker socket mount. Target source and ground truth are absent from the worker image.

## Reset and stop

```bash
docker compose restart ecommerce subscriptions warehouse complex
docker compose down
```

Dashboard sessions use UUID-keyed isolated fixture state through an administrator-enabled policy and the `X-Discovery-Session` header. The bounded target registry keeps at most 128 active namespaces with a 15-minute inactivity expiry, longer than the maximum 10-minute discovery budget. Concurrent sessions cannot reset each other. The HTTP benchmark still starts a fresh process for each run. Unnamespaced manual target calls share the default fixture. Do not restart a target during active sessions. PostgreSQL and artifact volumes survive ordinary shutdown. Removing volumes is destructive and is not part of the normal stop command.

## Generated artifacts

The web interface downloads artifacts after generation. Container validation remains a separate operator action. The worker does not control the host Docker daemon. Export an artifact directory and invoke `scripts.test_sandbox` from the workspace.

## Release verification and telemetry

```bash
conda run --no-capture-output -n api-discovery-ai python -m scripts.verify
```

The command uses `.env`, builds the stack and validator, exposes the disposable database on loopback port 15432 for integration tests, and runs the complete local release gate. The verification override is ignored under `.runtime/verification/compose.yml`. The report is `experiments/reports/release-checks.json`; the stack remains running. Stop the verification deployment with:

```bash
docker compose -f docker-compose.yml -f .runtime/verification/compose.yml down
```

Set `DISCOVERY_TELEMETRY=console` to export sanitized stage traces and metrics to worker stdout, then recreate the worker. Default `off` installs SDK providers without exporting. Console export uses only stage names, category, timing, session ID on spans, and a fixed service resource. Bodies, origins, headers, and exception messages are excluded. No hosted collector or provider account is required.

## Publication gate

Run all tests, dependency scans, and both secret scanners. Inspect staged content and Git history. Confirm `.env` files and runtime directories are ignored. Initialize and commit verified milestones only when Git metadata permissions are available.

Create a new public repository only after these checks pass. Use the authenticated GitHub account, do not overwrite an existing repository, and do not force-push. No repository has been created or published by the current execution.
