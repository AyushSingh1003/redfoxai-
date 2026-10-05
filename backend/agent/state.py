from typing import TypedDict, List, Dict, Any, Optional


class AssessmentState(TypedDict, total=False):
    assessment_id: str
    target: str
    profile: str
    authorized: bool
    status: str
    error: Optional[str]
    plan: List[str]
    plan_reason: Optional[str]
    tool_results: List[Dict[str, Any]]
    evidence_records: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    report_ready: bool
