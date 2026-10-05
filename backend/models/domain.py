from datetime import datetime
import json
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship

from database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, index=True)
    target = Column(String, index=True, nullable=False)
    profile = Column(String, nullable=False, default="safe_baseline")
    status = Column(String, nullable=False, default="queued")  # queued | running | completed | failed | rejected
    authorized = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    plan_json = Column(Text, nullable=True)  # JSON array of planned checks

    # Relationships
    events = relationship("AgentEvent", back_populates="assessment", cascade="all, delete-orphan", order_by="AgentEvent.order")
    tool_executions = relationship("ToolExecution", back_populates="assessment", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")


class AgentEvent(Base):
    __tablename__ = "assessment_events"

    id = Column(String, primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id"), index=True, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    event_type = Column(String, nullable=False, default="info")  # info | success | error | node
    message = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="events")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id = Column(String, primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id"), index=True, nullable=False)
    tool_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # running | completed | failed
    duration_ms = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    assessment = relationship("Assessment", back_populates="tool_executions")
    evidence_items = relationship("Evidence", back_populates="tool_execution")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True)
    assessment_id = Column(String, ForeignKey("assessments.id"), index=True, nullable=False)
    tool_execution_id = Column(String, ForeignKey("tool_executions.id"), nullable=True)
    evidence_type = Column(String, nullable=False)  # http_status | security_headers | cookie_attributes
    evidence_json = Column(Text, nullable=False)  # Structured JSON evidence
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="evidence_items")
    tool_execution = relationship("ToolExecution", back_populates="evidence_items")

    @property
    def data(self):
        try:
            return json.loads(self.evidence_json)
        except Exception:
            return {}


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, index=True)
    assessment_id = Column(String, ForeignKey("assessments.id"), index=True, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)  # headers | cookies | transport | reconnaissance
    severity = Column(String, nullable=False)  # Informational | Low | Medium | High
    confidence = Column(String, nullable=False, default="High")  # Low | Medium | High
    description = Column(Text, nullable=False)  # Verified deterministic observation
    evidence_reference = Column(String, nullable=True)  # Tool or evidence ID
    evidence_snapshot = Column(Text, nullable=True)  # Filtered JSON evidence slice
    why_it_matters = Column(Text, nullable=True)  # AI-generated or grounded explanation
    remediation = Column(Text, nullable=True)  # Remediation guidance
    verification_status = Column(String, nullable=False, default="verified")  # verified | unverified
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="findings")


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id = Column(String, primary_key=True)
    run_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_cases = Column(Integer, nullable=False)
    passed_cases = Column(Integer, nullable=False)
    failed_cases = Column(Integer, nullable=False)
    scope_compliance_rate = Column(Float, nullable=False)
    plan_validity_rate = Column(Float, nullable=False)
    evidence_fidelity_rate = Column(Float, nullable=False)
    avg_latency_ms = Column(Float, nullable=False)
    details_json = Column(Text, nullable=False)
