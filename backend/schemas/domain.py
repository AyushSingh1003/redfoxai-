from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AssessmentCreate(BaseModel):
    target: str = Field(..., description="Target URL, must match authorized local lab")
    profile: str = Field("safe_baseline", description="Assessment profile (safe_baseline)")
    authorized: bool = Field(..., description="Explicit acknowledgement of authorized scope")


class AssessmentResponse(BaseModel):
    id: str
    target: str
    profile: str
    status: str
    authorized: bool
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    plan: Optional[List[str]] = None


class AgentEventResponse(BaseModel):
    id: str
    assessment_id: str
    order: int
    kind: str  # info | success | error | node
    title: str
    detail: Optional[str] = None
    occurred_at: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: str
    assessment_id: str
    tool_execution_id: Optional[str] = None
    evidence_type: str
    evidence_data: Dict[str, Any]
    collected_at: Optional[str] = None


class FindingResponse(BaseModel):
    id: str
    assessment_id: str
    title: str
    category: str
    severity: str  # Informational | Low | Medium | High
    confidence: str
    description: str  # Verified observation
    evidence_reference: Optional[str] = None
    evidence_snapshot: Optional[Dict[str, Any]] = None
    why_it_matters: Optional[str] = None  # AI analysis
    remediation: Optional[str] = None  # Remediation guidance
    verification_status: str
    created_at: Optional[str] = None


class AssessmentReportResponse(BaseModel):
    assessment_id: str
    target: str
    profile: str
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    executive_summary: str
    timeline: List[Dict[str, Any]]
    checks_executed: List[Dict[str, Any]]
    findings_distribution: Dict[str, int]
    findings: List[FindingResponse]
    remediation_recommendations: List[Dict[str, str]]
    agent_evaluation_summary: Dict[str, Any]
    limitations: List[str]
    disclaimer: str


class SettingsResponse(BaseModel):
    app_name: str
    app_subtitle: str
    app_env: str
    lab_target: str
    agent_version: str
    allowed_tools: List[Dict[str, Any]]
    llm_provider: str
    llm_model: str
    llm_available: bool


class EvaluationTestCaseResult(BaseModel):
    case_name: str
    description: str
    passed: bool
    expected: str
    actual: str
    latency_ms: float
    notes: Optional[str] = None


class EvaluationResponse(BaseModel):
    id: str
    run_at: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    scope_compliance_rate: float
    plan_validity_rate: float
    evidence_fidelity_rate: float
    avg_latency_ms: float
    cases: List[EvaluationTestCaseResult]
