import uuid
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient

from main import app
from config import settings
from database import SessionLocal
from models.domain import Assessment, AgentEvent, ToolExecution, Evidence, Finding
from services.assessment_service import _execute_assessment_lifecycle

client = TestClient(app)


def test_complete_assessment_lifecycle_end_to_end():
    """
    Complete end-to-end integration test of the full assessment lifecycle:
    Scope -> Plan -> Policy Approval -> Deterministic Execution -> Evidence -> Findings -> Report -> Completion
    """
    db = SessionLocal()
    test_id = f"test-lifecycle-{uuid.uuid4()}"
    try:
        # Create test assessment record
        asm = Assessment(
            id=test_id,
            target=settings.LAB_TARGET,
            profile="safe_baseline",
            status="queued",
            authorized=True,
        )
        db.add(asm)
        db.commit()

        # Mock deterministic tool runs with rich responses
        mock_http = MagicMock()
        mock_http.status_code = 200
        mock_http.headers = httpx.Headers({
            "content-type": "text/html; charset=utf-8",
            "x-content-type-options": "nosniff",
            "set-cookie": "session_id=123; Path=/; HttpOnly; SameSite=Lax",
        })
        mock_http.content = b"<html>Demo</html>"
        mock_http.http_version = "HTTP/1.1"

        with patch("security_tools.runner.run_hardened_http_request", return_value=(mock_http, None, 12.0)):
            # Execute lifecycle synchronously inside test
            _execute_assessment_lifecycle(db, asm)

        db.refresh(asm)

        # 1. Verify terminal status
        assert asm.status == "completed"
        assert asm.started_at is not None
        assert asm.completed_at is not None

        # 2. Verify all lifecycle events persisted in correct order
        events = db.query(AgentEvent).filter(AgentEvent.assessment_id == asm.id).order_by(AgentEvent.order.asc()).all()
        assert len(events) >= 6
        event_titles = [e.message for e in events]
        assert any("Scope Validated" in t for t in event_titles)
        assert any("Plan Approved" in t for t in event_titles)
        assert any("Evidence Collected" in t for t in event_titles)
        assert any("Findings Cataloged" in t for t in event_titles)
        assert any("Report Generated" in t for t in event_titles)

        # 3. Verify tool executions & evidence persisted
        executions = db.query(ToolExecution).filter(ToolExecution.assessment_id == asm.id).all()
        assert len(executions) >= 3
        evidence_items = db.query(Evidence).filter(Evidence.assessment_id == asm.id).all()
        assert len(evidence_items) >= 3

        # 4. Verify findings cataloged
        findings = db.query(Finding).filter(Finding.assessment_id == asm.id).all()
        assert len(findings) >= 1
        for f in findings:
            assert f.verification_status == "verified"
            assert f.severity in ("Informational", "Low", "Medium", "High")

        # 5. Verify report endpoint returns compiled report
        report_res = client.get(f"/api/reports/{asm.id}")
        assert report_res.status_code == 200
        report_data = report_res.json()
        assert report_data["status"] == "completed"
        assert len(report_data["findings"]) >= 1
        assert "executive_summary" in report_data
        assert "disclaimer" in report_data

    finally:
        db.close()
