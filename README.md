# AEGIS — AI Agent Security Evaluation Platform

AEGIS is a full-stack, locally runnable workbench for evaluating AI-agent security behavior against a curated library of **synthetic adversarial scenarios**. It includes an interactive dashboard, agent registry, deterministic test engine, persisted evaluation history, risk metrics, and downloadable Markdown reports.

> **Scope:** This release is a working MVP with a deterministic simulator. It does not connect to live LLMs, execute external tools, access real secrets, or test third-party systems. The included attack scenarios run only against local demo profiles and synthetic canary data.

## Product capabilities

- **Overview dashboard** — agent count, evaluation history, average score, score trend, and recent activity.
- **Agent registry** — create profiles in `hardened` or `vulnerable` simulation mode and optionally enable mock tool access.
- **Scenario library** — six controlled tests covering direct prompt injection, sensitive data disclosure, unauthorized tool use, unsafe output handling, memory poisoning, and excessive agency.
- **Evaluation engine** — deterministic scenario execution, per-finding evidence, remediation advice, and severity-weighted metrics.
- **Evaluation history** — persisted results with detail views and downloadable Markdown reports.
- **API and interactive docs** — REST API plus FastAPI Swagger UI at `/docs`.
- **Delivery foundation** — Docker image, Compose file, and GitHub Actions test workflow.

## Technology

- Python 3.12+
- FastAPI + Pydantic
- SQLAlchemy 2
- SQLite by default; optional PostgreSQL support via `requirements-postgres.txt`
- HTML, CSS and vanilla JavaScript frontend
- Docker / Docker Compose
- Pytest + HTTPX

The frontend is intentionally dependency-light so the product can be run without a JavaScript package manager or paid service account.

## Quick start

### 1. Create an environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Start AEGIS

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. API documentation is available at **http://127.0.0.1:8000/docs**.

On first start, AEGIS creates two demo agents:

- **Hardened Demo Agent** — rejects the included simulated attack behaviors.
- **Vulnerable Demo Agent** — intentionally exhibits the included simulated weaknesses. Mock tool events are recorded only; no real action is performed.

The default database is `./aegis.db`. It is ignored by Git. For PostgreSQL, install `python -m pip install -r requirements-postgres.txt` and set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`.

## Run with Docker

```bash
docker compose up --build
```

Then open **http://localhost:8000**. The database is stored in the named `aegis-data` volume. The container runs as an unprivileged user, drops Linux capabilities, uses a read-only root filesystem, and keeps writable application data under `/data`.

## Run tests

```bash
pytest -q
```

Tests cover health, seeded agents, hardened and vulnerable outcomes, mock-tool permission behavior, invalid input handling, and Markdown report generation.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/overview` | Dashboard summary and recent activity |
| GET | `/api/agents` | List agent profiles |
| POST | `/api/agents` | Create a simulation profile |
| GET | `/api/scenarios` | List available test scenarios |
| POST | `/api/runs` | Execute a selected evaluation |
| GET | `/api/runs` | List recent evaluation runs |
| GET | `/api/runs/{id}` | Retrieve an evaluation and findings |
| GET | `/api/runs/{id}/report` | Download a Markdown report |

Example evaluation request:

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"agent_id": 1, "scenario_ids": ["direct_prompt_injection", "sensitive_data_disclosure"]}'
```

## Metrics and interpretation

- **Security score:** 100 minus severity-weighted simulated risk, normalized to the selected scenarios.
- **Attack success rate:** percentage of selected scenarios that the simulator marks as successful.
- **Defense pass rate:** percentage of selected scenarios blocked by the simulation profile.
- **Data leakage rate:** outcome rate for the data-protection scenario(s).
- **Unauthorized action rate:** outcome rate for mock tool/autonomy scenarios.

These are **AEGIS internal comparison metrics**, not an industry-standard benchmark, independent audit, certification, or evidence that a real model is secure. Compare agents only across the same scenario set and version.

## Repository layout

```text
.
├── app/
│   ├── main.py             # FastAPI routes and app factory
│   ├── database.py         # SQLAlchemy engine/session setup
│   ├── models.py           # Agent and evaluation persistence models
│   ├── schemas.py          # Request validation
│   ├── scenarios.py        # Synthetic scenario library
│   ├── engine.py           # Deterministic evaluation and scoring
│   └── static/             # Dashboard UI
├── docs/
│   ├── ARCHITECTURE.md
│   ├── THREAT_MODEL.md
│   └── ROADMAP.md
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## Publish to GitHub

See [`GITHUB_PUBLISH.md`](GITHUB_PUBLISH.md) for the commands to publish this project to a new, empty GitHub repository.

## Security notes before public deployment

This MVP is intended for local development and controlled demonstrations. Before exposing it to the public internet or connecting real models, add authentication and authorization, tenant isolation, CSRF protections where applicable, request rate limits, secrets management, database migrations, structured audit logs, production CORS policy, and an isolated execution boundary for every model/tool adapter. Never connect production credentials or real destructive tools to the current deterministic demo engine.

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the next engineering milestones: real model adapters, sandboxed tool adapters, richer evaluators, benchmark reproducibility, authentication/RBAC, PostgreSQL migrations, and CI security scanning.

## License

MIT — see [`LICENSE`](LICENSE).
