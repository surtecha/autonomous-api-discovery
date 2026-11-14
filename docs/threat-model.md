# Threat model

## Assets and actors

Protected assets include runtime credentials, local files, authorized target state, generated artifacts, session evidence, and repository history. Potential attackers include a malicious API server, hostile text inside API responses, a compromised model response, an unauthenticated control-plane caller, and a compromised dependency.

## Enforced controls

| Boundary | Threat | Implemented control |
| --- | --- | --- |
| Session API to target policy | Arbitrary target selection | Only registered target identifiers are accepted |
| Experiment to transport | SSRF and method escalation | Exact configured origin, explicit port, allowed method set, restricted relative-path grammar |
| DNS to socket | DNS rebinding | All resolved addresses must match pins, socket connects to approved numeric address |
| HTTPS connection | Hostname spoofing | TLS verification uses the configured original hostname |
| HTTP redirects | Credential forwarding and target escape | All redirects fail closed |
| Target response to evidence | Prompt injection and data leakage | Headers are discarded, arbitrary string values are replaced, sensitive keys are removed |
| Evidence to model | Instruction promotion | Only numeric selection metadata and approved method labels are transmitted |
| Model to execution | Arbitrary tool use | Model can select an existing candidate index only |
| Gateway to credentials | Secret disclosure | Credentials are resolved server-side and not added to observations |
| Attempt replay | Duplicate mutations | Write-ahead journal rejects uncertain interrupted attempts |
| Artifacts to execution | Host compromise | Separate non-root, read-only, networkless Docker validator with resource limits |
| Browser to API | Credential exposure | Server-side proxy attaches backend credential |
| Browser writes | CSRF | Same-origin checks on mutation requests |
| Control plane | Unauthorized use | Constant-time bearer-token check on API routes, web HTTP Basic authentication |
| Logs and traces | Secret capture | Allowlisted stage identifiers, duration, session ID, and result category only |

## Operational requirements

Docker images must be built before validation. The validator image must contain only approved dependencies. The validator is not invoked by mounting a Docker socket into the worker. An operator-side command runs it with a single read-only artifact mount.

Production access requires TLS in front of web HTTP Basic authentication. The default Compose published ports bind to loopback only. The target and control networks are internal. The worker has both networks because it needs database access and target access. Application-level origin and port restrictions remain necessary on both networks.

Target state must be reset by restarting target containers before an independent evaluation. The benchmark command starts a fresh local process for every strategy and target. Dashboard sessions use separate bounded UUID namespaces, starting with fresh target state; the default unnamespaced manual fixture remains process-scoped.

Dependency locks, vulnerability scans, Gitleaks, detect-secrets, and CI must pass before publication. The supplemental Python pattern scan is not a substitute for these scanners. No secret-bearing environment file is included in source.

## Residual risks and deployment boundaries

Local HTTP and TLS sockets, Docker validation, and container isolation have been exercised. Unit tests still use mocks to cover DNS rebinding and deterministic error cases. Live socket tests cover sanitization, malformed responses, redirects, response limits, original-host TLS verification, and hostname mismatches. The isolation suite checks non-root execution, read-only roots, missing application credentials and Docker socket, and unreachable target networking. These checks do not prove the absence of every container escape or malformed-server behavior.

Sanitization preserves numeric resource identifiers and a fixed vocabulary of control fields. Identifiers can be sensitive outside disposable environments. Arbitrary response keys can still disclose schema vocabulary to local evidence, although model input excludes those keys. The gateway should not be deployed against sensitive external data without a target-specific data policy.

String redaction sacrifices string-format inference. The generator uses deterministic source construction and AST parsing, but AST parsing is not a security proof. Generated tests must remain inside the validator even when generated code looks ordinary.

HTTP limits reduce resource exhaustion but do not prove resistance to every malformed server behavior. JSON parsing has a response-size bound and sanitization has depth and item bounds. Native parser behavior, TLS libraries, Docker, and dependency supply chains remain trusted components.

The frontend CSP permits inline Next.js scripts and inline styles. This is weaker than a nonce-based policy. Untrusted HTML is never rendered through an HTML insertion API.

There is no tenant isolation, external identity provider, distributed worker fencing, or artifact retention policy. This deployment is a single-operator development system, not a completed enterprise service.
