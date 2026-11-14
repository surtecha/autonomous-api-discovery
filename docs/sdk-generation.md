# SDK generation and validation

Generation uses deterministic Python source templates derived from structured observations. Paths and methods determine operation names. Pydantic models represent request and response fields. The client uses HTTPX with configurable base URL, timeout, optional runtime bearer token, disabled redirects, disabled environment proxy discovery, context management, and status-only exceptions.

Python keywords and reserved model attributes use generated attribute names with aliases that preserve the original wire fields. Serialization uses those aliases. Response models merge schemas across observed successful status codes. Required request fields use verified claims, consistently with OpenAPI generation.

The OpenAPI document uses version 3.1.0. Successful observed status codes become response entries. Request-required lists include verified omission claims only. `x-evidence` and `x-field-evidence` preserve provenance. Authentication is not invented when it has not been observed.

Generated source is parsed with `ast.parse` on the host. It is not imported or executed there. The artifact directory contains `client.py`, `pyproject.toml`, `fixtures.json`, `test_client.py`, `openapi.json`, and `validation.json`.

```bash
docker build -f infrastructure/docker/validator.Dockerfile -t api-discovery-validator:local .
conda run -n api-discovery-ai python -m scripts.test_sandbox .runtime/run/sdk
```

The runner executes Pytest, Ruff, strict Mypy, and package building in separate resource-limited containers. A writable tmpfs is used for build output. The source mount is read-only and restricted to the six generated bundle files. Extra files, subdirectories, and symlinks are rejected before Docker invocation. There is no host Docker socket, SSH directory, Git configuration, application configuration, or LLM credential mount.

Current generated tests use HTTPX mock transports and observed fixtures. They exercise generated methods, request serialization, response-model parsing, status errors, credential attachment, and required-model behavior. Generated collection methods accept optional cursor and limit values. `iter_<operation>_pages(max_pages=100)` yields typed pages, follows bounded same-collection cursor/limit links, rejects cycles, and caps traversal at 1,000 pages. External or unrelated links are never followed. Fresh-target live workflow tests run inside networkless validator containers; loopback is their only transport. A successful generation or AST parse does not imply SDK validation.

`validation.json` stores `not_run` until a validator actually executes. Docker absence is reported explicitly. A host fallback is intentionally not provided.

The validation command exits with status 1 unless every container check passes and reported test counts contain at least one test with no failures, errors, or skips. CI generates and validates all 12 fixture bundles. Static consistency, source lint, and strict typing have passed locally for all bundles; the live HTTP benchmark bundles also pass these checks and mock transport tests inside restricted containers. Separate live workflow verification is available through `python -m scripts.live_sdk`. It checks creation, pagination, status errors, and supported resource workflows for all four gain-strategy clients. The complex fixture checks only the observed account workflow; hidden job configuration is not invented.

The live validator mounts the generated bundle, trusted workflow tests, and disposable target implementation read-only. It starts and stops a fresh target subprocess for every test inside the container. No generated code executes on the host. Both baseline and live validation reject missing test counts, failures, errors, and skips. The HTTPX client configuration follows the [official client API](https://www.python-httpx.org/advanced/clients/).
