# AEGIS Architecture

## Runtime flow

```text
Browser UI (HTML / CSS / JS)
          |
          v
FastAPI REST layer (/api/*)
          |
          +---- Agent registry ------ SQLAlchemy ------ SQLite / PostgreSQL (optional driver)
          |
          +---- Scenario catalogue (versioned Python data)
          |
          +---- Evaluation engine
                    |
                    +---- deterministic demo-agent behavior
                    +---- scenario-specific evaluators
                    +---- severity-weighted metrics
                    +---- findings + remediation evidence
          |
          v
EvaluationRun persistence
          |
          +---- Dashboard history
          +---- JSON detail endpoint
          +---- Markdown report endpoint
```

## Design decisions

1. **Simulator-first:** the first release uses deterministic local profiles so expected behavior can be tested without model-provider credentials, external network calls, or unsafe tools.
2. **Explicit scenario metadata:** each test has an ID, category, severity, expected behavior, remediation, and synthetic evidence.
3. **Separation of concerns:** FastAPI routes handle validation and persistence; `engine.py` owns evaluation logic; `scenarios.py` owns the initial test catalogue.
4. **Reproducibility:** each evaluation stores scenario-level results and metric snapshots. Scenario versioning should be introduced before large benchmark suites are published.
5. **UI safety:** dynamic values are escaped before being inserted into HTML; simulator outputs are presented as text.

## Extension points

- Add `AgentAdapter` protocol for local model adapters.
- Add sandboxed `ToolAdapter` implementations with allowlisted mock tools.
- Replace heuristic outcomes with explicit evaluator functions and model-graded evaluations that include human review.
- Add a `ScenarioVersion` and `EvaluationConfig` record for benchmark reproducibility.
- Move from SQLite to PostgreSQL and add Alembic migrations for multi-user deployments.
