# Local LLM discovery verification — 15 November 2026

Downloaded and exercised Qwen2.5 7B (Q4_K_M) through Ollama 0.40.16 on Apple M3 Pro / 18 GiB. A real schema-constrained probe parsed successfully. Hosted OpenAI access was blocked by HTTP 429, error type `insufficient_quota`; no successful hosted call or verified provider bill is claimed.

## Comparison

80 fresh-process HTTP trials: four project-owned fixtures × four strategies × five repetitions; seeds 42–46, 100-request / 120-second fixture policies. Output directories were new. Existing benchmark reports were preserved.

LLM uses three bounded local-model calls followed by gain fallback. Temperature zero. Gain and FIFO repeats are deterministic controls. This is not a general model-quality or speed benchmark.

| Fixture | LLM / gain / FIFO operations | LLM / gain / FIFO requests | Random mean operations | Random mean requests | LLM transition coverage | LLM response type accuracy |
|---|---:|---:|---:|---:|---:|---:|
| ecommerce | 32/32 | 66 | 30.0 | 79.4 | 100% | 87.69% |
| subscriptions | 24/24 | 47 | 23.8 | 53.2 | 100% | 88.24% |
| warehouse | 32/32 | 71 | 30.4 | 76.0 | 100% | 87.59% |
| complex | 9/15 | 19 | 9.0 | 20.4 | 0% | 78.67% |

All local-model, gain and FIFO outcomes above were identical across five repetitions. All strategies had 100% endpoint precision and zero unsupported operation claims. Local-model request field type and requiredness accuracy were 100% on scored discovered fields; this does not score unknown missing fields. Complex recall remains 60%, with zero job-transition coverage because usable nested repair evidence is withheld.

Local-model-assisted discovery used 1,015 requests versus seeded random’s 1,145 across 20 runs (11.35% fewer), recovering 485 versus 466 correct operation instances. This advantage is shared with gain and FIFO; **no improvement over those strategies was observed**.

## Model usage and costs

60 calls, 60 valid parsed selections, zero failures, zero unmeasured calls; 31,165 reported tokens (30,645 input / 520 output). Aggregate provider-call time: 48.893 seconds. The separate successful 7B probe used 84 tokens; these totals exclude exploratory 3B and hosted diagnostics. No provider API fee applies to local inference ($0); hardware, electricity, and download costs were not measured. Failed hosted calls have no reported token usage and no verified bill.

## Verification

All 80 generated SDK bundles passed 4,914 restricted-container tests, Ruff, strict Mypy, package builds, AST and OpenAPI generation checks. Static artifact consistency passed for all 84 new bundles including four hosted-quota fallback diagnostics. Python regression: 73 passed, zero skipped, 28 subtests passed, including PostgreSQL and Docker isolation. Python Ruff and Mypy passed, including modified scripts. Bandit found no medium/high issues; four low-severity findings remain. Python and frontend dependency audits reported no known vulnerabilities; the unpublished project package itself is not in PyPI’s advisory database. Secret scanner results are recorded separately. Frontend production/browser checks and the entire release command were not rerun; this report does not supersede the earlier complete release gate.

## Resume-ready evidence

- Built and evaluated a bounded local-LLM API discovery workflow across 80 fresh-process trials, recovering 97/103 fixture operations with 100% endpoint precision and validating 80 generated SDKs through 4,914 isolated tests.
- Integrated schema-constrained Qwen2.5 7B inference with 60/60 valid parsed selections and zero model failures; matched gain/FIFO coverage and used 11.35% fewer requests than seeded random across four fixtures.

These figures describe project-owned fixtures and a three-call ranking budget. They do not establish production-scale performance, fully autonomous contract synthesis, or superiority over gain/FIFO.

## Evidence

- `comparison.json`: all 80 evaluations, per-group mean/range/sample deviation, model usage and validation.
- `probe-7b.json`, `provenance.json`: parsed probe, model digests, runtime archive checksum and sources.
- `hosted-provider-diagnosis.json`: sanitized provider failure evidence.
- `artifact-consistency.json`, `checks.json`: validation and regression evidence.
- Raw baseline trials: `../comparison-20261115/`. Local LLM trials: `../local-llm-comparison-20261115/`. Hosted fallback diagnostics: `../llm-quota-20261115/`.

Official references: [Ollama compatibility](https://docs.ollama.com/api/openai-compatibility), [model](https://ollama.com/library/qwen2.5:7b).
