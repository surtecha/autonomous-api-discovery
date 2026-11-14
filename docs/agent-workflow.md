# Agent workflow

The graph contains separate ranking, gateway execution, and evidence update nodes. Graph state is a typed dictionary containing serializable domain state. Each successful graph update persists evidence separately from the checkpoint.

Experiments include a method, relative path, optional JSON body, hypothesis, expected observation, gain estimate, cost estimate, safety label, parent observation, and controlled perturbation metadata. Safety labels are descriptive. The gateway enforces permissions independently.

## Candidate generation

The initial candidate is `GET /`, or explicit seed paths in the core initializer. Advertised relative links create new candidates. Collection links also produce bounded OPTIONS requests. Structured validation errors suggest field types and required inputs. Reference errors can reuse previously observed identifiers. State and quantity conflicts are deferred until a successful mutation changes the available evidence.

The engine does not enumerate a dictionary of resource names or arbitrary paths. No discovery is possible when the target supplies neither usable seeds nor affordances. A negative response is retained without declaring the endpoint nonexistent.

## Ranking

The gain strategy uses `(estimated_gain + novelty + omission_verification_bonus) / cost`. Novelty is 1.0 for an operation without a successful observation and 0.2 otherwise. Controlled omission checks receive a 1.5 bonus. These are hand-selected heuristic weights, not Bayesian posterior probabilities.

FIFO and seeded random selectors share the same candidate generator and policy. Type perturbations, failed requests, and verification requests count toward the same request budget. Experiment fingerprints include explicit verification context so a deliberate omission can repeat an earlier request shape.

## Optional model ranking

The OpenAI structured-output adapter can select one of at most 20 candidate indices. It receives method, estimated gain, estimated cost, omission status, and successful operation count. It receives no response bodies, request values, paths, origins, headers, or credentials.

The output schema permits only a bounded integer index. Missing output, invalid indices, provider errors, and timeouts fall back to deterministic ranking. Provider retries are disabled. A session reserves 2,048 budget tokens before each model call and stops before the 8,000-token reservation ceiling. Reservations and call counts are persisted before provider execution and retained after failures or graph replay. Reported `tokens` count only provider-reported usage. Unmeasured calls and conservative budget reservations are reported separately. Reservations are not provider billing measurements.

The Docker worker has no Internet egress and does not receive an LLM credential by default. Hosted-model execution requires a separately reviewed egress deployment. No hosted-model result has been measured in the current environment.
