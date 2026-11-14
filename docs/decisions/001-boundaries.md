# ADR 001: Deterministic security outside model reasoning

Status: implemented and verified.

The model selects an existing candidate index. It cannot supply network destinations, credentials, shell commands, file paths, or policy overrides. This reduces the authority of compromised model output. Gateway validation remains mandatory even for deterministic candidates.

# ADR 002: LangGraph with a write-ahead HTTP journal

Status: implemented and verified with persistence and resume tests using a controlled fixture transport.

Graph checkpoints preserve workflow state but do not make external HTTP writes transactional. A separate attempt journal records intent before execution. Uncertain writes stop instead of replaying. SQLite provides a local durable implementation. PostgreSQL remains the control-plane job database. Distributed execution requires a different coordinated persistence design.

# ADR 003: Deterministic SDK generation

Status: implemented with AST checks and restricted container tests, typing, packaging, and live workflows.

Source generation uses validated observation structures and fixed code templates. No model-generated executable source is accepted. AST parsing detects syntax failures. Execution remains isolated in Docker because deterministic generation does not eliminate implementation defects.

# ADR 004: Controlled fixtures and separate evaluation

Status: fixtures, structural response scorer, and 12-run live HTTP benchmark verified locally.

Local disposable targets permit repeatable mutations without accessing third-party infrastructure. The worker image excludes fixture source and hidden contracts. The evaluator reads hidden contracts only after exploration. In-process development diagnostics are labeled separately because they do not enforce the process boundary.

# ADR 005: Pinned transport instead of a general HTTPX discovery client

Status: implemented and covered by mocked transport plus live HTTP/TLS tests.

The discovery gateway uses Python's HTTP transport with explicit numeric socket destinations and original-host TLS validation. This avoids a second DNS lookup between policy validation and connection establishment. Redirects and proxy discovery are absent. HTTPX remains the generated SDK transport. Live TLS verification, malformed-response checks, and restricted container network checks pass locally.
