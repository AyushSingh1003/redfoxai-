import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.domain import Finding, Evidence
from llm.client import ollama_client
from rag.knowledge_base import knowledge_retriever


def derive_deterministic_findings(
    tool_name: str,
    evidence_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based observation engine.
    Derives facts strictly from evidence without hallucinations.
    """
    findings_spec = []

    if tool_name == "http_status":
        status_code = evidence_data.get("status_code")
        latency = evidence_data.get("latency_ms", 0)
        content_type = evidence_data.get("content_type", "unknown")
        findings_spec.append({
            "title": f"HTTP Service Baseline Observed ({status_code})",
            "category": "reconnaissance",
            "severity": "Informational",
            "confidence": "High",
            "description": f"Verified endpoint availability responding with HTTP {status_code} in {latency}ms. Declared Content-Type: {content_type}.",
            "evidence_snapshot": {
                "status_code": status_code,
                "latency_ms": latency,
                "content_type": content_type,
            },
            "default_why": "Baseline HTTP service inspection confirms the network port is open and responding. Informational finding for scope confirmation.",
            "default_remediation": "Ensure administrative interfaces and internal debugging endpoints are protected with authentication and not exposed inadvertently.",
        })

    elif tool_name == "security_headers":
        missing = evidence_data.get("missing_headers", [])
        present = evidence_data.get("present_headers", {})

        if "content-security-policy" in missing:
            findings_spec.append({
                "title": "Missing Content-Security-Policy (CSP) Header",
                "category": "headers",
                "severity": "Medium",
                "confidence": "High",
                "description": "Verified observation: The response lacks a Content-Security-Policy header. Browsers have no restrictions on untrusted script origins.",
                "evidence_snapshot": {
                    "missing_header": "content-security-policy",
                    "total_missing": len(missing),
                },
                "default_why": "Without CSP, cross-site scripting (XSS) attacks can execute scripts from arbitrary third-party domains and exfiltrate data.",
                "default_remediation": "Deploy a restrictive Content-Security-Policy header, such as: default-src 'self'; script-src 'self'; object-src 'none'.",
            })

        if "strict-transport-security" in missing:
            findings_spec.append({
                "title": "Missing HTTP Strict Transport Security (HSTS)",
                "category": "headers",
                "severity": "Low",
                "confidence": "High",
                "description": "Verified observation: Strict-Transport-Security header was not detected on the response.",
                "evidence_snapshot": {
                    "missing_header": "strict-transport-security",
                },
                "default_why": "HSTS instructs browsers to strictly use HTTPS. Without it, clients may be vulnerable to SSL stripping man-in-the-middle attacks.",
                "default_remediation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' to all HTTPS responses.",
            })

        if "x-content-type-options" in missing:
            findings_spec.append({
                "title": "Missing X-Content-Type-Options Header",
                "category": "headers",
                "severity": "Low",
                "confidence": "High",
                "description": "Verified observation: X-Content-Type-Options header is absent, allowing browsers to perform MIME-type sniffing.",
                "evidence_snapshot": {
                    "missing_header": "x-content-type-options",
                },
                "default_why": "MIME sniffing allows browsers to execute non-script resources as script if they contain executable text.",
                "default_remediation": "Configure web server or application middleware to return 'X-Content-Type-Options: nosniff'.",
            })

    elif tool_name == "cookie_attributes":
        cookies = evidence_data.get("cookies", [])
        insecure_cookies = [
            c for c in cookies
            if not c.get("secure") or not c.get("httponly") or not c.get("samesite")
        ]

        if insecure_cookies:
            flag_issues = []
            for c in insecure_cookies:
                cname = c.get("cookie_name", "unknown")
                missing_flags = []
                if not c.get("secure"):
                    missing_flags.append("Secure")
                if not c.get("httponly"):
                    missing_flags.append("HttpOnly")
                if not c.get("samesite"):
                    missing_flags.append("SameSite")
                flag_issues.append(f"{cname} (missing: {', '.join(missing_flags)})")

            findings_spec.append({
                "title": "Insecure Cookie Attribute Configuration",
                "category": "cookies",
                "severity": "Medium",
                "confidence": "High",
                "description": f"Verified observation: Found {len(insecure_cookies)} cookie(s) missing security flags: {'; '.join(flag_issues)}.",
                "evidence_snapshot": {
                    "insecure_count": len(insecure_cookies),
                    "cookies_flagged": insecure_cookies,
                },
                "default_why": "Missing HttpOnly allows JavaScript cookie theft via XSS; missing Secure permits transmission over cleartext; missing SameSite increases CSRF risk.",
                "default_remediation": "Ensure all Set-Cookie directives specify '; Secure; HttpOnly; SameSite=Lax' (or Strict).",
            })

    return findings_spec


def generate_and_persist_findings(
    db: Session,
    assessment_id: str,
    tool_name: str,
    evidence_id: str,
    evidence_data: Dict[str, Any],
) -> List[Finding]:
    """
    Derives deterministic findings from evidence, optionally enriches with AI analysis,
    and persists them to the database.
    """
    specs = derive_deterministic_findings(tool_name, evidence_data)
    persisted = []

    # Attempt AI enrichment if LLM is reachable
    llm_available = ollama_client.check_availability()

    for spec in specs:
        why_it_matters = spec["default_why"]
        remediation = spec["default_remediation"]

        if llm_available:
            ai_analysis = ollama_client.analyze_evidence(
                tool_name=tool_name,
                evidence=spec["evidence_snapshot"],
            )
            if ai_analysis:
                why_it_matters = f"[AI Analysis Grounded in Evidence]\n{ai_analysis.why_it_matters}"
                remediation = f"[AI Recommended Remediation]\n{ai_analysis.remediation}"
            else:
                why_it_matters = f"[Deterministic RAG Guidance (LLM skipped)]\n{spec['default_why']}"
                remediation = f"[Standard Remediation]\n{spec['default_remediation']}"
        else:
            why_it_matters = f"[Deterministic Guidance (AI unavailable)]\n{spec['default_why']}"
            remediation = f"[Standard Remediation]\n{spec['default_remediation']}"

        finding = Finding(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            title=spec["title"],
            category=spec["category"],
            severity=spec["severity"],
            confidence=spec["confidence"],
            description=spec["description"],
            evidence_reference=evidence_id,
            evidence_snapshot=json.dumps(spec["evidence_snapshot"]),
            why_it_matters=why_it_matters,
            remediation=remediation,
            verification_status="verified",
        )
        db.add(finding)
        persisted.append(finding)

    db.flush()
    return persisted
