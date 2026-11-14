# Evaluation methodology and results

## Matching and scoring

An operation is the exact uppercase method plus canonical path. Numeric path segments become `{id}`; version prefixes remain literal. Precision divides correctly matched observed operations by reported operations; recall divides matched operations by the independent contract. Root and OPTIONS operations count when the fixture implements them. Zero denominators produce null.

Request-field type and required-field accuracy compare discovered top-level request fields with the independent contract. Required claims need controlled omission evidence. Undiscovered operations reduce recall but do not enter the field denominator, so these field scores can be optimistic.

Response-schema accuracy compares structural type claims at object properties and array-item paths, including nested shapes and type unions, against independent response schemas. Extra and missing type claims are penalized; integer observations are compatible with a number contract. It scores discovered operations and successful response statuses, excludes values and requiredness, and reports the denominator as `response_schema_type_claims`. Empty arrays leave item types unknown and can lower accuracy. This metric is not a proof of a complete response contract.

Transition coverage matches verified `(operation, from_state, to_state)` tuples. A self-transition counts only when the operation succeeds and prior resource state is known. Provider cost stays null without measured usage and configured pricing. SDK pass rates use actual container test counts, including failures, errors, and skips.

## Real loopback HTTP benchmarks

All 12 target/strategy combinations execute through LangGraph and the pinned HTTP gateway. Each starts a fresh target process on an available loopback port. The scorer loads independent ground truth only after discovery. Every SDK bundle passes tests, lint, strict Mypy, and packaging in restricted containers. Complete per-run evidence, policies, scores, validation, timing, and the aggregate summary reside in `experiments/reports/http`.

Gain-strategy results under a 100-request limit:

| Target | Correct operations | Requests | Precision | Recall | Transition coverage | Response type accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E-commerce | 32 / 32 | 66 | 1.000 | 1.000 | 1.000 | 0.877 |
| Subscriptions | 24 / 24 | 47 | 1.000 | 1.000 | 1.000 | 0.882 |
| Warehouse | 32 / 32 | 71 | 1.000 | 1.000 | 1.000 | 0.876 |
| Complex | 9 / 15 | 19 | 1.000 | 0.600 | 0.000 | 0.787 |

The complex target returns ambiguous configuration errors without actionable nested-input evidence. Unsuccessful operations stay undiscovered. These failures are retained in the benchmark. No general gain-strategy improvement is claimed from four fixtures and one deterministic random schedule.

## In-process diagnostics and live client checks

`experiments/reports/fixture-diagnostics` uses fresh target objects and the same inference engine, with sanitized handler calls in process. It does not establish a network boundary and remains separately labeled. Its artifacts are validated in restricted containers by the release gate.

`python -m scripts.live_sdk` additionally exercises each gain client against fresh target subprocesses inside networkless validator containers. Checks cover live creation and reads, multiple pagination pages, status exceptions, and the observed resource workflows. The complex client covers its observed account contract only. External networking is unavailable; loopback remains available inside each container. No generated code executes on the host.

## Reproduction

```bash
conda run -n api-discovery-ai python -m scripts.fixture_diagnostics
docker build -f infrastructure/docker/validator.Dockerfile -t api-discovery-validator:local .
conda run -n api-discovery-ai python -m scripts.live_sdk
conda run -n api-discovery-ai python -m scripts.benchmark --output experiments/reports/http
```

The worker image excludes fixture source and ground truth, giving stronger source separation than host benchmark orchestration. Hosted-provider variants require a separate authorized configuration and are not part of the local release measurements.
