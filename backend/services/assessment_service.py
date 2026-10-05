from datetime import datetime
import json
import threading
import time
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from database import SessionLocal
from models.domain import Assessment, AgentEvent, ToolExecution, Evidence, Finding
from agent.graph import assessment_graph
from services.evidence_service import record_tool_execution
from services.finding_service import generate_and_persist_findings
from security_tools.base import ToolResult

_WORKER_LOCK = threading.Lock()
_RUNNING: set[str] = set()

TERMINAL_STATUSES = {"completed", "failed", "rejected"}


def record_event(
    db: Session,
    assessment_id: str,
    *,
    kind: str,
    title: str,
    detail: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentEvent:
    max_order = (
        db.query(AgentEvent.order)
        .filter(AgentEvent.assessment_id == assessment_id)
        .order_by(AgentEvent.order.desc())
        .limit(1)
        .scalar()
    ) or 0

    event = AgentEvent(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        order=max_order + 1,
        event_type=kind,
        message=title,
        detail=detail,
        metadata_json=json.dumps(metadata) if metadata else None,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.flush()
    return event


def set_assessment_status(
    db: Session,
    assessment_id: str,
    status: str,
    error: Optional[str] = None,
) -> Assessment:
    a = db.query(Assessment).filter(Assessment.id == assessment_id).one()
    a.status = status
    if status == "running" and not a.started_at:
        a.started_at = datetime.utcnow()
    elif status in TERMINAL_STATUSES and not a.completed_at:
        a.completed_at = datetime.utcnow()
    if error:
        a.error = error
    db.flush()
    return a


def start_assessment_worker(assessment_id: str) -> None:
    with _WORKER_LOCK:
        if assessment_id in _RUNNING:
            return
        _RUNNING.add(assessment_id)

    def _runner():
        db = SessionLocal()
        try:
            assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
            if not assessment:
                return
            _execute_assessment_lifecycle(db, assessment)
            db.commit()
        except Exception as e:
            try:
                db.rollback()
                set_assessment_status(db, assessment_id, "failed", error=str(e))
                record_event(
                    db,
                    assessment_id,
                    kind="error",
                    title="Unexpected Assessment Failure",
                    detail=str(e),
                )
                db.commit()
            except Exception:
                pass
        finally:
            try:
                db.close()
            finally:
                with _WORKER_LOCK:
                    _RUNNING.discard(assessment_id)

    thread = threading.Thread(target=_runner, name=f"redfox-asm-{assessment_id[:8]}", daemon=True)
    thread.start()


def _execute_assessment_lifecycle(db: Session, a: Assessment) -> None:
    set_assessment_status(db, a.id, "running")
    record_event(
        db,
        a.id,
        kind="info",
        title="Assessment Started",
        detail=f"Target: {a.target} | Profile: {a.profile}",
    )
    db.flush()

    initial_state = {
        "assessment_id": a.id,
        "target": a.target,
        "profile": a.profile,
        "authorized": bool(a.authorized),
    }

    state_agg = dict(initial_state)

    for step_output in assessment_graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_update in step_output.items():
            state_agg.update(node_update or {})
            node_status = node_update.get("status")

            if node_name == "validate_scope":
                if node_status == "scope_validated":
                    record_event(
                        db,
                        a.id,
                        kind="success",
                        title="Scope Validated",
                        detail=f"Verified target within authorized lab: {a.target}",
                    )
                elif node_status == "rejected":
                    err = node_update.get("error", "Scope rejected")
                    record_event(
                        db,
                        a.id,
                        kind="error",
                        title="Scope Validation Rejected",
                        detail=err,
                    )
                    set_assessment_status(db, a.id, "rejected", error=err)
                    db.commit()
                    return

            elif node_name == "generate_plan":
                plan = node_update.get("plan", [])
                reason = node_update.get("plan_reason", "")
                a.plan_json = json.dumps(plan)
                db.flush()
                record_event(
                    db,
                    a.id,
                    kind="node",
                    title="Assessment Plan Generated",
                    detail=f"Planned checks ({len(plan)}): {', '.join(plan)}\nReason: {reason}",
                )

            elif node_name == "validate_plan":
                if node_status == "plan_approved":
                    record_event(
                        db,
                        a.id,
                        kind="success",
                        title="Plan Approved by Policy Engine",
                        detail="All proposed tools validated against authorized tool registry.",
                    )
                elif node_status == "rejected":
                    err = node_update.get("error", "Plan rejected by policy engine")
                    record_event(
                        db,
                        a.id,
                        kind="error",
                        title="Plan Rejected by Policy Engine",
                        detail=err,
                    )
                    set_assessment_status(db, a.id, "rejected", error=err)
                    db.commit()
                    return

            elif node_name == "execute_tools":
                tool_results = node_update.get("tool_results", [])
                for r in tool_results:
                    t_res = ToolResult(
                        tool_name=r["tool_name"],
                        status=r["status"],
                        evidence=r["evidence"],
                        message=r["message"],
                        duration_ms=r.get("duration_ms", 0.0),
                        error=r.get("error"),
                    )
                    # Persist ToolExecution and Evidence
                    exec_rec = record_tool_execution(db, a.id, t_res)
                    # Derive and persist findings
                    generate_and_persist_findings(
                        db,
                        assessment_id=a.id,
                        tool_name=r["tool_name"],
                        evidence_id=exec_rec.id,
                        evidence_data=r["evidence"],
                    )

                    t_kind = "success" if r["status"] == "completed" else "error"
                    record_event(
                        db,
                        a.id,
                        kind=t_kind,
                        title=f"Check: {r['tool_name']} {r['status']}",
                        detail=f"{r['message']} ({r.get('duration_ms', 0)}ms)",
                    )

            elif node_name == "collect_evidence":
                records = node_update.get("evidence_records", [])
                record_event(
                    db,
                    a.id,
                    kind="info",
                    title="Evidence Collected",
                    detail=f"Structured evidence cataloged for {len(records)} tool run(s).",
                )

            elif node_name == "verify_evidence":
                record_event(
                    db,
                    a.id,
                    kind="success",
                    title="Evidence Integrity Verified",
                    detail="Evidence payloads validated against schemas and bounds.",
                )

            elif node_name == "analyze_evidence":
                record_event(
                    db,
                    a.id,
                    kind="node",
                    title="AI Evidence Analysis",
                    detail="Analyzing observations with security guidance retrieval.",
                )

            elif node_name == "generate_findings":
                findings = (
                    db.query(Finding)
                    .filter(Finding.assessment_id == a.id)
                    .all()
                )
                record_event(
                    db,
                    a.id,
                    kind="success",
                    title="Findings Cataloged",
                    detail=f"Generated and verified {len(findings)} finding(s) grounded strictly in evidence.",
                )

            elif node_name == "generate_report":
                record_event(
                    db,
                    a.id,
                    kind="success",
                    title="Assessment Report Generated",
                    detail="Comprehensive security assessment report and executive summary compiled.",
                )

            db.flush()

    # Finalize status
    final_status = state_agg.get("status", "completed")
    if final_status not in TERMINAL_STATUSES:
        final_status = "completed"

    set_assessment_status(db, a.id, final_status)
    record_event(
        db,
        a.id,
        kind="success" if final_status == "completed" else "error",
        title=f"Assessment {final_status.capitalize()}",
        detail="Assessment workflow finished.",
    )
    db.commit()


def recover_in_flight(db: Session) -> None:
    stuck = db.query(Assessment).filter(Assessment.status.in_(["queued", "running"])).all()
    for a in stuck:
        a.status = "failed"
        a.error = "Assessment interrupted by server restart."
        a.completed_at = datetime.utcnow()
        record_event(
            db,
            a.id,
            kind="error",
            title="Assessment Terminated on Server Restart",
            detail="Process restarted while assessment was in flight. Marked failed to prevent stale spinners.",
        )
    if stuck:
        db.commit()
