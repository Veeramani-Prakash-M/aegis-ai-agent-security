# AEGIS Engineering Roadmap

## Release 1.0 — Local simulator MVP (included)

- Interactive dashboard and agent registry
- Six synthetic agent-security scenarios graded by evaluators that inspect agent output
- Deterministic hardened/vulnerable profiles
- Severity-weighted score and rate metrics
- Persistent run history and Markdown reports
- FastAPI REST API, tests, Docker and CI workflow

## Release 1.1 — Evaluation quality (partly included)

- Done: scenario library version recorded on each run; evaluator contract and per-scenario unit tests with false-positive / false-negative fixtures; agent deletion and run filtering
- Scenario IDs with semantic versioning
- Repeat runs, seeds, config snapshots and reproducible benchmark bundles
- Larger labelled fixture corpus for evaluator accuracy tracking
- CSV and JSON report export

## Release 1.2 — Model adapters

- Provider-neutral adapter interface (the `AgentAdapter` protocol exists; only the simulator implements it)
- One local model integration first, then optional hosted providers
- Timeouts, retry budgets, usage limits and prompt redaction
- Human-reviewed evaluator outputs; model-graded scores never treated as ground truth

## Release 1.3 — Safe tool simulation

- Allowlisted mock tools with JSON schemas
- Policy engine for identity, scope, approval and least privilege
- Tool-call trace and authorization decision audit log
- Isolated worker process with resource limits

## Release 2.0 — Multi-user platform

- PostgreSQL and Alembic migrations
- Authentication, RBAC, tenant isolation and audit logging
- Background job queue and run cancellation
- Team workspaces, versioned agents and benchmark comparisons
- Deployment automation, observability and security scanning

## Acceptance standard for a release

Every release should include passing tests, reproducible instructions, documented limitations, a threat-model update, and evidence for any performance or security claim made in its README or resume description.
