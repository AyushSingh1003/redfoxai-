from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy.orm import Session

from models.domain import Assessment, AgentEvent, ToolExecution, Evidence, Finding


def seed_demo_data(db: Session) -> Assessment:
    """
    Creates a clearly labeled demonstration assessment record.
    All records explicitly specify [DEMO DATA] to maintain absolute integrity.
    """
    demo_id = str(uuid.uuid4())
    now = datetime.utcnow()
    started = now - timedelta(minutes=5)
    completed = now - timedelta(minutes=4)

    assessment = Assessment(
        id=demo_id,
        target="http://juice-shop:3000 (DEMO DATASET)",
        profile="safe_baseline",
        status="completed",
        authorized=True,
        created_at=started - timedelta(seconds=10),
        started_at=started,
        completed_at=completed,
        plan_json=json.dumps(["http_status", "security_headers", "cookie_attributes"]),
    )
    db.add(assessment)
    db.flush()

    # Demo events
    events_data = [
        ("info", "Assessment Started", "DEMO DATA: Initialized baseline security check.", 1),
        ("success", "Scope Validated", "DEMO DATA: Target scope verified within local training lab.", 2),
        ("node", "Assessment Plan Generated", "DEMO DATA: Planned checks: http_status, security_headers, cookie_attributes", 3),
        ("success", "Plan Approved by Policy Engine", "DEMO DATA: All planned checks approved by policy engine.", 4),
        ("success", "Check: http_status completed", "DEMO DATA: HTTP 200 OK received in 18ms", 5),
        ("success", "Check: security_headers completed", "DEMO DATA: Inspected 6 headers (2 present, 4 missing)", 6),
        ("success", "Check: cookie_attributes completed", "DEMO DATA: 1 cookie inspected, missing Secure flag", 7),
        ("info", "Evidence Collected", "DEMO DATA: Structured evidence collected and normalized.", 8),
        ("success", "Evidence Integrity Verified", "DEMO DATA: Evidence verified against schema.", 9),
        ("node", "AI Evidence Analysis", "DEMO DATA: AI analyzed observations with RAG security guidance.", 10),
        ("success", "Findings Cataloged", "DEMO DATA: 3 demonstration findings cataloged.", 11),
        ("success", "Assessment Completed", "DEMO DATA: Demonstration workflow finished.", 12),
    ]

    for kind, title, detail, order in events_data:
        evt = AgentEvent(
            id=str(uuid.uuid4()),
            assessment_id=demo_id,
            order=order,
            event_type=kind,
            message=f"[DEMO DATA] {title}",
            detail=detail,
            timestamp=started + timedelta(seconds=order * 5),
        )
        db.add(evt)

    # Demo Tool Executions & Evidence
    t1_id = str(uuid.uuid4())
    t1 = ToolExecution(
        id=t1_id,
        assessment_id=demo_id,
        tool_name="http_status",
        status="completed",
        duration_ms=18.4,
        started_at=started + timedelta(seconds=15),
        completed_at=started + timedelta(seconds=16),
    )
    db.add(t1)

    ev1 = Evidence(
        id=str(uuid.uuid4()),
        assessment_id=demo_id,
        tool_execution_id=t1_id,
        evidence_type="http_status",
        evidence_json=json.dumps({
            "status_code": 200,
            "latency_ms": 18.4,
            "content_type": "text/html; charset=utf-8",
            "is_demo_data": True,
        }),
        collected_at=started + timedelta(seconds=16),
    )
    db.add(ev1)

    t2_id = str(uuid.uuid4())
    t2 = ToolExecution(
        id=t2_id,
        assessment_id=demo_id,
        tool_name="security_headers",
        status="completed",
        duration_ms=22.1,
        started_at=started + timedelta(seconds=20),
        completed_at=started + timedelta(seconds=21),
    )
    db.add(t2)

    ev2 = Evidence(
        id=str(uuid.uuid4()),
        assessment_id=demo_id,
        tool_execution_id=t2_id,
        evidence_type="security_headers",
        evidence_json=json.dumps({
            "present_headers": {"x-content-type-options": "nosniff"},
            "missing_headers": ["content-security-policy", "strict-transport-security"],
            "is_demo_data": True,
        }),
        collected_at=started + timedelta(seconds=21),
    )
    db.add(ev2)

    # Demo Findings
    f1 = Finding(
        id=str(uuid.uuid4()),
        assessment_id=demo_id,
        title="[DEMO DATA] Missing Content-Security-Policy (CSP) Header",
        category="headers",
        severity="Medium",
        confidence="High",
        description="[DEMO DATA RECORD] Verified observation: Content-Security-Policy header is absent.",
        evidence_reference=ev2.id,
        evidence_snapshot=json.dumps({"missing": "content-security-policy", "is_demo": True}),
        why_it_matters="[DEMO DATA ANALYSIS] Without CSP, malicious scripts injected via stored or reflected XSS can execute in victims' browsers.",
        remediation="[DEMO DATA GUIDANCE] Deploy a restrictive CSP header: default-src 'self'.",
        verification_status="verified",
        created_at=started + timedelta(seconds=35),
    )
    db.add(f1)

    f2 = Finding(
        id=str(uuid.uuid4()),
        assessment_id=demo_id,
        title="[DEMO DATA] Missing HTTP Strict Transport Security (HSTS)",
        category="headers",
        severity="Low",
        confidence="High",
        description="[DEMO DATA RECORD] Verified observation: Strict-Transport-Security header is absent.",
        evidence_reference=ev2.id,
        evidence_snapshot=json.dumps({"missing": "strict-transport-security", "is_demo": True}),
        why_it_matters="[DEMO DATA ANALYSIS] HSTS prevents downgrade attacks from HTTPS to cleartext HTTP.",
        remediation="[DEMO DATA GUIDANCE] Set 'Strict-Transport-Security: max-age=31536000; includeSubDomains'.",
        verification_status="verified",
        created_at=started + timedelta(seconds=36),
    )
    db.add(f2)

    db.commit()
    db.refresh(assessment)
    return assessment
