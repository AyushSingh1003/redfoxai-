import pytest
from fastapi.testclient import TestClient

from main import app
from config import settings

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["app"] == settings.APP_NAME


def test_settings_endpoint():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["lab_target"] == settings.LAB_TARGET
    assert len(data["allowed_tools"]) == 3
    # Ensure no secrets leaked
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()


def test_create_assessment_success():
    res = client.post(
        "/api/assessments",
        json={
            "target": settings.LAB_TARGET,
            "profile": "safe_baseline",
            "authorized": True,
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["target"] == settings.LAB_TARGET
    assert data["status"] in ("queued", "running", "completed")


def test_create_assessment_rejected_unauthorized():
    res = client.post(
        "/api/assessments",
        json={
            "target": settings.LAB_TARGET,
            "profile": "safe_baseline",
            "authorized": False,  # Not checked
        },
    )
    assert res.status_code == 403
    assert "authorization acknowledgement required" in res.json()["detail"].lower()


def test_create_assessment_rejected_external_target():
    res = client.post(
        "/api/assessments",
        json={
            "target": "https://google.com",
            "profile": "safe_baseline",
            "authorized": True,
        },
    )
    assert res.status_code == 403
    assert "outside the authorized local lab boundary" in res.json()["detail"].lower()


def test_list_and_get_assessments():
    # List assessments
    res = client.get("/api/assessments")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0

    asm_id = res.json()[0]["id"]
    single_res = client.get(f"/api/assessments/{asm_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == asm_id


def test_get_assessment_not_found():
    res = client.get("/api/assessments/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_list_findings_and_filters():
    res = client.get("/api/findings")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    filtered = client.get("/api/findings?severity=Medium")
    assert filtered.status_code == 200


def test_seed_demo_data():
    res = client.post("/api/demo/seed")
    assert res.status_code == 200
    data = res.json()
    assert "DEMO" in data["target"]
    assert data["status"] == "completed"

    # Verify report is accessible for demo
    rep_res = client.get(f"/api/reports/{data['id']}")
    assert rep_res.status_code == 200
    assert len(rep_res.json()["findings"]) >= 1
    assert "educational security assessment" in rep_res.json()["disclaimer"].lower()


def test_evaluation_endpoints():
    run_res = client.post("/api/evaluation/run")
    assert run_res.status_code == 200
    eval_data = run_res.json()
    assert eval_data["total_cases"] == 6
    assert eval_data["passed_cases"] == 6
    assert eval_data["scope_compliance_rate"] == 1.0

    latest_res = client.get("/api/evaluation/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["total_cases"] == 6
