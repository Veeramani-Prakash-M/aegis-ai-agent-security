from fastapi.testclient import TestClient

from app.main import create_app


def make_client():
    app = create_app("sqlite://")
    return TestClient(app)


def test_health_and_seed_agents():
    client = make_client()
    assert client.get("/api/health").json()["status"] == "ok"
    agents = client.get("/api/agents").json()
    assert len(agents) == 2
    assert {agent["mode"] for agent in agents} == {"hardened", "vulnerable"}


def test_hardened_agent_blocks_all_default_scenarios():
    client = make_client()
    agents = client.get("/api/agents").json()
    hardened = next(agent for agent in agents if agent["mode"] == "hardened")
    response = client.post("/api/runs", json={"agent_id": hardened["id"]})
    assert response.status_code == 201
    result = response.json()
    assert result["score"] == 100.0
    assert result["attack_success_rate"] == 0.0
    assert result["blocked"] == 6
    assert result["vulnerable"] == 0


def test_vulnerable_agent_exposes_expected_simulated_findings():
    client = make_client()
    agents = client.get("/api/agents").json()
    vulnerable = next(agent for agent in agents if agent["mode"] == "vulnerable")
    response = client.post("/api/runs", json={"agent_id": vulnerable["id"]})
    assert response.status_code == 201
    result = response.json()
    assert result["score"] == 0.0
    assert result["attack_success_rate"] == 100.0
    assert result["vulnerable"] == 6


def test_tool_attacks_depend_on_tool_permission():
    client = make_client()
    created = client.post("/api/agents", json={
        "name": "Vulnerable but tool restricted", "mode": "vulnerable", "allow_tools": False
    }).json()
    response = client.post("/api/runs", json={
        "agent_id": created["id"], "scenario_ids": ["unauthorized_tool_use", "excessive_agency"]
    })
    assert response.status_code == 201
    assert response.json()["vulnerable"] == 0


def test_unknown_agent_and_scenario_are_rejected():
    client = make_client()
    assert client.post("/api/runs", json={"agent_id": 9999}).status_code == 404
    agent = client.get("/api/agents").json()[0]
    assert client.post("/api/runs", json={"agent_id": agent["id"], "scenario_ids": ["not-real"]}).status_code == 422


def test_report_is_downloadable_markdown():
    client = make_client()
    agent = client.get("/api/agents").json()[0]
    run = client.post("/api/runs", json={"agent_id": agent["id"]}).json()
    report = client.get(f"/api/runs/{run['id']}/report")
    assert report.status_code == 200
    assert "AEGIS Security Evaluation Report" in report.text
    assert "Scope and limitations" in report.text


def test_selected_scenarios_only_affect_that_run():
    client = make_client()
    vulnerable = next(agent for agent in client.get("/api/agents").json() if agent["mode"] == "vulnerable")
    response = client.post("/api/runs", json={
        "agent_id": vulnerable["id"],
        "scenario_ids": ["direct_prompt_injection", "unsafe_output_handling"],
    })
    assert response.status_code == 201
    result = response.json()
    assert result["total"] == 2
    assert result["vulnerable"] == 2
    assert result["attack_success_rate"] == 100.0


def test_created_agent_is_persisted_and_listed():
    client = make_client()
    response = client.post("/api/agents", json={
        "name": "Read-only Evaluation Agent",
        "description": "A custom local test profile",
        "provider": "Local simulator",
        "mode": "hardened",
        "allow_tools": False,
    })
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Read-only Evaluation Agent"
    assert any(agent["id"] == created["id"] for agent in client.get("/api/agents").json())
