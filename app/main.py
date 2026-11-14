from __future__ import annotations

import json
import os
from datetime import timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .database import Base, build_database, get_session
from .engine import evaluate_agent
from .models import Agent, EvaluationRun
from .scenarios import SCENARIOS, get_scenarios
from .schemas import AgentCreate, EvaluationCreate

STATIC_DIR = Path(__file__).parent / "static"


def iso(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def serialize_agent(agent: Agent) -> dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "provider": agent.provider,
        "mode": agent.mode,
        "allow_tools": agent.allow_tools,
        "created_at": iso(agent.created_at),
    }


def serialize_run(run: EvaluationRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "agent_id": run.agent_id,
        "agent_name": run.agent.name if run.agent else "Unknown agent",
        "score": run.score,
        "attack_success_rate": run.attack_success_rate,
        "total": run.total,
        "blocked": run.blocked,
        "vulnerable": run.vulnerable,
        "created_at": iso(run.created_at),
        "metrics": json.loads(run.metrics_json),
        "results": json.loads(run.results_json),
    }


def create_app(database_url: str | None = None) -> FastAPI:
    engine, session_factory = build_database(database_url)
    Base.metadata.create_all(bind=engine)
    with session_factory() as seed_db:
        if seed_db.scalar(select(Agent).limit(1)) is None:
            seed_db.add_all([
                Agent(
                    name="Hardened Demo Agent",
                    description="Strict demo profile that rejects every included adversarial scenario.",
                    provider="Local deterministic simulator",
                    mode="hardened",
                    allow_tools=False,
                ),
                Agent(
                    name="Vulnerable Demo Agent",
                    description="Intentionally weak demo profile for validating whether AEGIS detects known test failures.",
                    provider="Local deterministic simulator",
                    mode="vulnerable",
                    allow_tools=True,
                ),
            ])
            seed_db.commit()

    app = FastAPI(
        title="AEGIS API",
        version="1.0.0",
        description="Synthetic AI-agent security evaluation API. Only evaluates the included demo agent profiles.",
    )
    app.state.session_factory = session_factory
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def db_dependency():
        yield from get_session(app.state.session_factory)

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "AEGIS API", "version": "1.0.0"}

    @app.get("/api/overview")
    def overview(db: Session = Depends(db_dependency)):
        agents = db.scalars(select(Agent).order_by(Agent.id)).all()
        runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(8)).all()
        all_runs = db.scalars(select(EvaluationRun)).all()
        average = round(sum(r.score for r in all_runs) / len(all_runs), 1) if all_runs else None
        return {
            "agent_count": len(agents),
            "run_count": len(all_runs),
            "average_score": average,
            "scenario_count": len(SCENARIOS),
            "agents": [serialize_agent(agent) for agent in agents],
            "recent_runs": [serialize_run(run) for run in runs],
        }

    @app.get("/api/agents")
    def list_agents(db: Session = Depends(db_dependency)):
        return [serialize_agent(agent) for agent in db.scalars(select(Agent).order_by(Agent.id)).all()]

    @app.post("/api/agents", status_code=201)
    def create_agent(payload: AgentCreate, db: Session = Depends(db_dependency)):
        agent = Agent(**payload.model_dump())
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return serialize_agent(agent)

    @app.get("/api/scenarios")
    def list_scenarios():
        return get_scenarios()

    @app.post("/api/runs", status_code=201)
    def create_run(payload: EvaluationCreate, db: Session = Depends(db_dependency)):
        agent = db.get(Agent, payload.agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        known_ids = {scenario["id"] for scenario in SCENARIOS}
        selected_ids = payload.scenario_ids
        if selected_ids is not None:
            unknown = sorted(set(selected_ids) - known_ids)
            if unknown:
                raise HTTPException(status_code=422, detail=f"Unknown scenario IDs: {', '.join(unknown)}")
            if not selected_ids:
                raise HTTPException(status_code=422, detail="Select at least one scenario")
        evaluation = evaluate_agent(agent, selected_ids)
        metrics = evaluation["metrics"]
        run = EvaluationRun(
            agent_id=agent.id,
            score=metrics["security_score"],
            attack_success_rate=metrics["attack_success_rate"],
            total=metrics["scenario_count"],
            blocked=metrics["blocked_count"],
            vulnerable=metrics["vulnerable_count"],
            results_json=json.dumps(evaluation["results"]),
            metrics_json=json.dumps(metrics),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return serialize_run(run)

    @app.get("/api/runs")
    def list_runs(limit: int = 30, db: Session = Depends(db_dependency)):
        limit = max(1, min(limit, 100))
        runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit)).all()
        return [serialize_run(run) for run in runs]

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: int, db: Session = Depends(db_dependency)):
        run = db.get(EvaluationRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found")
        return serialize_run(run)

    @app.get("/api/runs/{run_id}/report", response_class=PlainTextResponse)
    def get_report(run_id: int, db: Session = Depends(db_dependency)):
        run = db.get(EvaluationRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found")
        results = json.loads(run.results_json)
        metrics = json.loads(run.metrics_json)
        lines = [
            f"# AEGIS Security Evaluation Report — Run #{run.id}",
            "",
            f"- Agent: {run.agent.name}",
            f"- Created: {iso(run.created_at)}",
            f"- Security score: {run.score}/100 (internal demo metric; not a certification)",
            f"- Attack success rate: {run.attack_success_rate}%",
            f"- Scenarios: {run.total} | Blocked: {run.blocked} | Vulnerable: {run.vulnerable}",
            "",
            "## Metric summary",
        ]
        for key, value in metrics.items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        lines.extend(["", "## Findings", ""])
        for result in results:
            lines.extend([
                f"### {result['name']} — {result['outcome']}",
                f"- Category: {result['category']} | Severity: {result['severity']}",
                f"- Attack: {result['attack_summary']}",
                f"- Expected: {result['expected_behavior']}",
                f"- Observed: {result['observed_behavior']}",
                f"- Remediation: {result['remediation']}",
                f"- Evidence: {result['evidence']}",
                "",
            ])
        lines.extend([
            "## Scope and limitations",
            "This report was generated by AEGIS's deterministic synthetic simulator. It does not test a live external model, execute real tools, access real secrets or certify a system as secure.",
        ])
        return "\n".join(lines)

    return app


app = create_app()
