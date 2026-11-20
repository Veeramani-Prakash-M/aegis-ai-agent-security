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


def test_health_reports_versions():
    body = make_client().get("/api/health").json()
    assert body["version"] and body["scenario_library"]


def test_invalid_agent_and_empty_scenario_selection_are_rejected():
    client = make_client()
    assert client.post("/api/agents", json={"name": "x"}).status_code == 422
    assert client.post("/api/agents", json={"name": "Valid name", "mode": "chaotic"}).status_code == 422
    agent = client.get("/api/agents").json()[0]
    assert client.post("/api/runs", json={"agent_id": agent["id"], "scenario_ids": []}).status_code == 422


def test_run_detail_contains_agent_response_and_metrics():
    client = make_client()
    vulnerable = next(a for a in client.get("/api/agents").json() if a["mode"] == "vulnerable")
    run = client.post("/api/runs", json={"agent_id": vulnerable["id"]}).json()
    detail = client.get(f"/api/runs/{run['id']}").json()
    assert detail["metrics"]["library_version"]
    assert all(result["agent_response"] for result in detail["results"])
    assert client.get("/api/runs/9999").status_code == 404
    assert client.get("/api/runs/9999/report").status_code == 404


def test_runs_can_be_filtered_by_agent():
    client = make_client()
    first, second = client.get("/api/agents").json()
    client.post("/api/runs", json={"agent_id": first["id"]})
    client.post("/api/runs", json={"agent_id": second["id"]})
    only_first = client.get("/api/runs", params={"agent_id": first["id"]}).json()
    assert len(only_first) == 1 and only_first[0]["agent_id"] == first["id"]
    assert len(client.get("/api/runs").json()) == 2


def test_deleting_an_agent_removes_its_runs():
    client = make_client()
    created = client.post("/api/agents", json={"name": "Temporary agent"}).json()
    client.post("/api/runs", json={"agent_id": created["id"]})
    assert client.delete(f"/api/agents/{created['id']}").status_code == 204
    assert all(a["id"] != created["id"] for a in client.get("/api/agents").json())
    assert client.get("/api/runs", params={"agent_id": created["id"]}).json() == []
    assert client.delete(f"/api/agents/{created['id']}").status_code == 404
    assert client.get("/api/overview").status_code == 200


def test_report_lists_agent_response_and_library_version():
    client = make_client()
    agent = next(a for a in client.get("/api/agents").json() if a["mode"] == "vulnerable")
    run = client.post("/api/runs", json={"agent_id": agent["id"]}).json()
    report = client.get(f"/api/runs/{run['id']}/report").text
    assert "Agent response:" in report
    assert "Scenario library: v" in report


def test_dashboard_and_static_assets_are_served():
    client = make_client()
    assert "AEGIS" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
