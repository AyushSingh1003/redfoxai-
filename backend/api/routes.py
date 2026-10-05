import asyncio
import json
import uuid
from typing import List, Optional, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db, SessionLocal
from models.domain import Assessment, AgentEvent, Finding, EvaluationRecord
from schemas.domain import (
    AssessmentCreate,
    AssessmentResponse,
    AgentEventResponse,
    FindingResponse,
    AssessmentReportResponse,
    SettingsResponse,
    EvaluationResponse,
)
from policy.scope import validate_scope_strict
from security_tools.registry import tool_registry
from llm.client import ollama_client
from services.assessment_service import (
    start_assessment_worker,
    record_event,
    TERMINAL_STATUSES,
)
from services.report_service import generate_assessment_report
from services.evaluation_service import run_evaluation_suite
from services.demo_service import seed_demo_data

router = APIRouter()

SSE_POLL_INTERVAL = 0.3


def _assessment_to_schema(a: Assessment) -> AssessmentResponse:
    plan = None
    if a.plan_json:
        try:
            plan = json.loads(a.plan_json)
        except Exception:
            plan = None
    return AssessmentResponse(
        id=a.id,
        target=a.target,
        profile=a.profile,
        status=a.status,
        authorized=bool(a.authorized),
        created_at=a.created_at.isoformat() if a.created_at else None,
        started_at=a.started_at.isoformat() if a.started_at else None,
        completed_at=a.completed_at.isoformat() if a.completed_at else None,
        error=a.error,
        plan=plan,
    )


def _event_to_dict(e: AgentEvent) -> dict:
    return {
        "id": e.id,
        "assessment_id": e.assessment_id,
        "order": e.order,
        "kind": e.event_type,
        "title": e.message,
        "detail": e.detail,
        "occurred_at": e.timestamp.isoformat() if e.timestamp else None,
    }


def _finding_to_schema(f: Finding) -> FindingResponse:
    snapshot = None
    if f.evidence_snapshot:
        try:
            snapshot = json.loads(f.evidence_snapshot)
        except Exception:
            snapshot = {"raw": f.evidence_snapshot}
    return FindingResponse(
        id=f.id,
        assessment_id=f.assessment_id,
        title=f.title,
        category=f.category,
        severity=f.severity,
        confidence=f.confidence,
        description=f.description,
        evidence_reference=f.evidence_reference,
        evidence_snapshot=snapshot,
        why_it_matters=f.why_it_matters,
        remediation=f.remediation,
        verification_status=f.verification_status,
        created_at=f.created_at.isoformat() if f.created_at else None,
    )


# ---------------------------------------------------------------------------
# Settings & Configuration
# ---------------------------------------------------------------------------
@router.get("/settings", response_model=SettingsResponse)
def get_system_settings():
    llm_online = ollama_client.check_availability()
    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_subtitle=settings.APP_SUBTITLE,
        app_env=settings.APP_ENV,
        lab_target=settings.LAB_TARGET,
        agent_version=settings.AGENT_VERSION,
        allowed_tools=tool_registry.list_tools(),
        llm_provider="Ollama (Local)",
        llm_model=settings.OLLAMA_MODEL,
        llm_available=llm_online,
    )


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------
@router.post("/assessments", response_model=AssessmentResponse, status_code=201)
def create_assessment(request: AssessmentCreate, db: Session = Depends(get_db)):
    is_valid, reason = validate_scope_strict(request.target, request.authorized)
    if not is_valid:
        raise HTTPException(status_code=403, detail=reason)

    if request.profile != settings.ALLOWED_PROFILE:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported profile '{request.profile}'. Allowed: {settings.ALLOWED_PROFILE}",
        )

    assessment = Assessment(
        id=str(uuid.uuid4()),
        target=request.target,
        profile=request.profile,
        status="queued",
        authorized=True,
    )
    db.add(assessment)
    db.flush()

    record_event(
        db,
        assessment.id,
        kind="info",
        title="Assessment Queued",
        detail="Assessment job queued for LangGraph background worker.",
    )
    db.commit()
    db.refresh(assessment)

    # Launch background worker
    start_assessment_worker(assessment.id)

    return _assessment_to_schema(assessment)


@router.get("/assessments", response_model=List[AssessmentResponse])
def list_assessments(db: Session = Depends(get_db)):
    assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    return [_assessment_to_schema(a) for a in assessments]


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _assessment_to_schema(a)


# ---------------------------------------------------------------------------
# Events & SSE Streaming
# ---------------------------------------------------------------------------
async def _generate_sse_stream(assessment_id: str) -> AsyncIterator[str]:
    yield ": redfox sse stream\nretry: 1500\n\n"
    db = SessionLocal()
    try:
        a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not a:
            err = json.dumps({"error": "Assessment not found", "id": assessment_id})
            yield f"event: error\ndata: {err}\n\n"
            yield 'event: done\ndata: {"final_status": "404"}\n\n'
            return

        events = (
            db.query(AgentEvent)
            .filter(AgentEvent.assessment_id == assessment_id)
            .order_by(AgentEvent.order.asc())
            .all()
        )
        last_order = 0
        for e in events:
            last_order = max(last_order, e.order)
            data = json.dumps(_event_to_dict(e), ensure_ascii=False)
            yield f"event: event\ndata: {data}\n\n"

        quiet_loops = 0
        max_quiet = int(600 / SSE_POLL_INTERVAL)

        while True:
            db.refresh(a)
            if a.status in TERMINAL_STATUSES:
                final_events = (
                    db.query(AgentEvent)
                    .filter(AgentEvent.assessment_id == assessment_id)
                    .filter(AgentEvent.order > last_order)
                    .order_by(AgentEvent.order.asc())
                    .all()
                )
                for e in final_events:
                    last_order = max(last_order, e.order)
                    data = json.dumps(_event_to_dict(e), ensure_ascii=False)
                    yield f"event: event\ndata: {data}\n\n"

                final_payload = json.dumps({"assessment_id": a.id, "final_status": a.status})
                yield f"event: done\ndata: {final_payload}\n\n"
                return

            newer = (
                db.query(AgentEvent)
                .filter(AgentEvent.assessment_id == assessment_id)
                .filter(AgentEvent.order > last_order)
                .order_by(AgentEvent.order.asc())
                .all()
            )
            if newer:
                quiet_loops = 0
                for e in newer:
                    last_order = max(last_order, e.order)
                    data = json.dumps(_event_to_dict(e), ensure_ascii=False)
                    yield f"event: event\ndata: {data}\n\n"
            else:
                quiet_loops += 1
                if quiet_loops % 15 == 0:
                    yield ": keepalive\n\n"
                if quiet_loops > max_quiet:
                    yield 'event: done\ndata: {"final_status": "timeout"}\n\n'
                    return

            db.commit()
            await asyncio.sleep(SSE_POLL_INTERVAL)
    except asyncio.CancelledError:
        return
    finally:
        db.close()


@router.get("/assessments/{assessment_id}/events")
def get_assessment_events(
    assessment_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # Support SSE directly if client requests text/event-stream
    accept = request.headers.get("accept", "")
    if "text/event-stream" in accept:
        return StreamingResponse(
            _generate_sse_stream(assessment_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    events = (
        db.query(AgentEvent)
        .filter(AgentEvent.assessment_id == assessment_id)
        .order_by(AgentEvent.order.asc())
        .all()
    )
    return [_event_to_dict(e) for e in events]


@router.get("/assessments/{assessment_id}/stream")
def stream_assessment_events(assessment_id: str):
    return StreamingResponse(
        _generate_sse_stream(assessment_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
@router.get("/findings", response_model=List[FindingResponse])
def list_findings(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    assessment_id: Optional[str] = Query(None, description="Filter by assessment"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity.ilike(severity))
    if assessment_id:
        query = query.filter(Finding.assessment_id == assessment_id)
    if category:
        query = query.filter(Finding.category.ilike(category))

    findings = query.order_by(Finding.created_at.desc()).all()
    return [_finding_to_schema(f) for f in findings]


@router.get("/findings/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return _finding_to_schema(finding)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@router.get("/reports/{assessment_id}", response_model=AssessmentReportResponse)
def get_report(assessment_id: str, db: Session = Depends(get_db)):
    report = generate_assessment_report(db, assessment_id)
    if not report:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return report


# ---------------------------------------------------------------------------
# Agent Evaluation
# ---------------------------------------------------------------------------
@router.post("/evaluation/run", response_model=EvaluationResponse)
def run_evaluation(db: Session = Depends(get_db)):
    return run_evaluation_suite(db)


@router.get("/evaluation/latest", response_model=EvaluationResponse)
def get_latest_evaluation(db: Session = Depends(get_db)):
    latest = (
        db.query(EvaluationRecord)
        .order_by(EvaluationRecord.run_at.desc())
        .first()
    )
    if not latest:
        # Run suite to initialize baseline
        return run_evaluation_suite(db)

    try:
        cases_raw = json.loads(latest.details_json)
    except Exception:
        cases_raw = []

    return EvaluationResponse(
        id=latest.id,
        run_at=latest.run_at.isoformat(),
        total_cases=latest.total_cases,
        passed_cases=latest.passed_cases,
        failed_cases=latest.failed_cases,
        scope_compliance_rate=latest.scope_compliance_rate,
        plan_validity_rate=latest.plan_validity_rate,
        evidence_fidelity_rate=latest.evidence_fidelity_rate,
        avg_latency_ms=latest.avg_latency_ms,
        cases=cases_raw,
    )


# ---------------------------------------------------------------------------
# Demonstration Data
# ---------------------------------------------------------------------------
@router.post("/demo/seed", response_model=AssessmentResponse)
def seed_demo(db: Session = Depends(get_db)):
    demo = seed_demo_data(db)
    return _assessment_to_schema(demo)
