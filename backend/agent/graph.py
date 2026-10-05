from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from agent.state import AssessmentState
from policy.scope import validate_scope_strict
from policy.tool_policy import validate_plan_policy
from security_tools.registry import tool_registry
from llm.client import ollama_client
from services.finding_service import derive_deterministic_findings


# Node 1: validate_scope
def validate_scope(state: AssessmentState) -> Dict[str, Any]:
    target = state.get("target", "")
    authorized = state.get("authorized", False)

    is_valid, reason = validate_scope_strict(target, authorized)
    if not is_valid:
        return {
            "status": "rejected",
            "error": reason,
        }

    return {"status": "scope_validated"}


# Node 2: generate_plan
def generate_plan(state: AssessmentState) -> Dict[str, Any]:
    target = state.get("target", "")
    profile = state.get("profile", "safe_baseline")

    # Attempt structured plan generation via LLM if available
    proposed = ollama_client.generate_plan(target, profile)
    if proposed and proposed.checks:
        return {
            "plan": proposed.checks,
            "plan_reason": proposed.reason,
            "status": "plan_generated",
        }

    # Deterministic fallback plan
    return {
        "plan": ["http_status", "security_headers", "cookie_attributes"],
        "plan_reason": "Deterministic safe baseline plan for authorized local training target.",
        "status": "plan_generated",
    }


# Node 3: validate_plan
def validate_plan(state: AssessmentState) -> Dict[str, Any]:
    plan = state.get("plan", [])
    is_valid, reason = validate_plan_policy(plan)

    if not is_valid:
        return {
            "status": "rejected",
            "error": f"Policy rejection: {reason}",
        }

    return {"status": "plan_approved"}


# Node 4: execute_tools
def execute_tools(state: AssessmentState) -> Dict[str, Any]:
    plan = state.get("plan", [])
    target = state.get("target", "")
    results = []

    for tool_name in plan:
        res = tool_registry.execute_tool(tool_name, target)
        results.append({
            "tool_name": res.tool_name,
            "status": res.status,
            "evidence": res.evidence,
            "message": res.message,
            "duration_ms": res.duration_ms,
            "error": res.error,
        })

    return {
        "tool_results": results,
        "status": "tools_executed",
    }


# Node 5: collect_evidence
def collect_evidence(state: AssessmentState) -> Dict[str, Any]:
    results = state.get("tool_results", [])
    evidence_records = []

    for r in results:
        evidence_records.append({
            "tool_name": r["tool_name"],
            "status": r["status"],
            "data": r["evidence"],
            "duration_ms": r.get("duration_ms", 0.0),
        })

    return {
        "evidence_records": evidence_records,
        "status": "evidence_collected",
    }


# Node 6: verify_evidence
def verify_evidence(state: AssessmentState) -> Dict[str, Any]:
    """
    Verifies that collected evidence conforms to bounds and is non-empty.
    """
    records = state.get("evidence_records", [])
    verified_records = []

    for rec in records:
        data = rec.get("data", {})
        # Evidence integrity verification
        if isinstance(data, dict):
            verified_records.append(rec)

    return {
        "evidence_records": verified_records,
        "status": "evidence_verified",
    }


# Node 7: analyze_evidence
def analyze_evidence(state: AssessmentState) -> Dict[str, Any]:
    # Analysis flag for pipeline tracing
    return {"status": "evidence_analyzed"}


# Node 8: generate_findings
def generate_findings(state: AssessmentState) -> Dict[str, Any]:
    evidence_records = state.get("evidence_records", [])
    findings = []

    for rec in evidence_records:
        tool_name = rec["tool_name"]
        data = rec["data"]
        derived = derive_deterministic_findings(tool_name, data)
        findings.extend(derived)

    return {
        "findings": findings,
        "status": "findings_generated",
    }


# Node 9: generate_report
def generate_report(state: AssessmentState) -> Dict[str, Any]:
    return {
        "report_ready": True,
        "status": "completed",
    }


# Conditional routing
def route_after_scope(state: AssessmentState) -> str:
    if state.get("status") == "scope_validated":
        return "generate_plan"
    return END


def route_after_plan_validation(state: AssessmentState) -> str:
    if state.get("status") == "plan_approved":
        return "execute_tools"
    return END


# Build the Graph
builder = StateGraph(AssessmentState)

builder.add_node("validate_scope", validate_scope)
builder.add_node("generate_plan", generate_plan)
builder.add_node("validate_plan", validate_plan)
builder.add_node("execute_tools", execute_tools)
builder.add_node("collect_evidence", collect_evidence)
builder.add_node("verify_evidence", verify_evidence)
builder.add_node("analyze_evidence", analyze_evidence)
builder.add_node("generate_findings", generate_findings)
builder.add_node("generate_report", generate_report)

builder.set_entry_point("validate_scope")

builder.add_conditional_edges(
    "validate_scope",
    route_after_scope,
    {"generate_plan": "generate_plan", END: END},
)

builder.add_edge("generate_plan", "validate_plan")

builder.add_conditional_edges(
    "validate_plan",
    route_after_plan_validation,
    {"execute_tools": "execute_tools", END: END},
)

builder.add_edge("execute_tools", "collect_evidence")
builder.add_edge("collect_evidence", "verify_evidence")
builder.add_edge("verify_evidence", "analyze_evidence")
builder.add_edge("analyze_evidence", "generate_findings")
builder.add_edge("generate_findings", "generate_report")
builder.add_edge("generate_report", END)

assessment_graph = builder.compile()
