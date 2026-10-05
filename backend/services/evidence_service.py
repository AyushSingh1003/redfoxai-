from datetime import datetime
import json
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models.domain import ToolExecution, Evidence
from security_tools.base import ToolResult


def record_tool_execution(
    db: Session,
    assessment_id: str,
    tool_result: ToolResult,
) -> ToolExecution:
    """
    Persists a deterministic tool execution record and its structured evidence.
    """
    execution_id = str(uuid.uuid4())
    execution = ToolExecution(
        id=execution_id,
        assessment_id=assessment_id,
        tool_name=tool_result.tool_name,
        status=tool_result.status,
        duration_ms=tool_result.duration_ms,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error=tool_result.error,
    )
    db.add(execution)
    db.flush()

    # Record Evidence
    evidence_id = str(uuid.uuid4())
    evidence = Evidence(
        id=evidence_id,
        assessment_id=assessment_id,
        tool_execution_id=execution_id,
        evidence_type=tool_result.tool_name,
        evidence_json=json.dumps(tool_result.evidence, ensure_ascii=False),
        collected_at=datetime.utcnow(),
    )
    db.add(evidence)
    db.flush()

    return execution
