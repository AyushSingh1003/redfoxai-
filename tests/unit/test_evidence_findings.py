from services.finding_service import derive_deterministic_findings
from rag.knowledge_base import knowledge_retriever


def test_derive_findings_from_missing_headers():
    evidence = {
        "present_headers": {"x-content-type-options": "nosniff"},
        "missing_headers": ["content-security-policy", "strict-transport-security"],
    }
    findings = derive_deterministic_findings("security_headers", evidence)
    assert len(findings) == 2
    titles = [f["title"] for f in findings]
    assert any("Content-Security-Policy" in t for t in titles)
    assert any("Strict Transport Security" in t for t in titles)
    # Ensure severity is reasonable (Medium/Low), never auto-escalated to Critical
    for f in findings:
        assert f["severity"] in ("Informational", "Low", "Medium")
        assert f["confidence"] == "High"
        assert "description" in f


def test_derive_findings_from_insecure_cookies():
    evidence = {
        "cookie_count": 1,
        "cookies": [{
            "cookie_name": "sid",
            "secure": False,
            "httponly": False,
            "samesite": False,
            "samesite_value": None,
        }],
        "has_insecure_flags": True,
    }
    findings = derive_deterministic_findings("cookie_attributes", evidence)
    assert len(findings) == 1
    assert "Insecure Cookie Attribute" in findings[0]["title"]
    assert findings[0]["severity"] == "Medium"


def test_rag_knowledge_retriever():
    results = knowledge_retriever.retrieve("content-security-policy script-src", category="security_headers")
    assert len(results) >= 1
    assert "CSP" in results[0]["title"] or "Content Security Policy" in results[0]["title"]
