import pytest
from policy.scope import is_target_allowed, validate_scope_strict, normalize_target
from policy.tool_policy import validate_plan_policy, ALLOWED_TOOLS


def test_normalize_target():
    assert normalize_target("http://juice-shop:3000/") == "http://juice-shop:3000"
    assert normalize_target("  http://juice-shop:3000  ") == "http://juice-shop:3000"
    assert normalize_target("") == ""


def test_scope_validation_authorized():
    # Authorized target with confirmation
    is_valid, reason = validate_scope_strict("http://juice-shop:3000", authorized=True)
    assert is_valid is True
    assert "verified" in reason.lower()


def test_scope_validation_unauthorized_user():
    # Target is valid lab, but user did NOT acknowledge authorization
    is_valid, reason = validate_scope_strict("http://juice-shop:3000", authorized=False)
    assert is_valid is False
    assert "authorization acknowledgement required" in reason.lower()


def test_scope_validation_external_target_blocked():
    # Public domains must fail closed
    targets = [
        "https://google.com",
        "http://evil-attacker.com",
        "http://192.168.1.1:8080",
        "https://owasp.org",
        "http://169.254.169.254/latest/meta-data/",  # Cloud metadata SSRF
    ]
    for target in targets:
        assert is_target_allowed(target) is False
        is_valid, reason = validate_scope_strict(target, authorized=True)
        assert is_valid is False
        assert "outside the authorized local lab boundary" in reason.lower()


def test_tool_policy_valid_plan():
    valid_plan = ["http_status", "security_headers", "cookie_attributes"]
    is_valid, reason = validate_plan_policy(valid_plan)
    assert is_valid is True
    assert "verified" in reason.lower()


def test_tool_policy_rejects_empty_plan():
    is_valid, reason = validate_plan_policy([])
    assert is_valid is False


def test_tool_policy_rejects_arbitrary_tools():
    malicious_plans = [
        ["bash", "http_status"],
        ["sqlmap", "security_headers"],
        ["nmap", "-sV", "http://juice-shop:3000"],
        ["curl", "http://attacker.com"],
        ["os.system('id')"],
    ]
    for plan in malicious_plans:
        is_valid, reason = validate_plan_policy(plan)
        assert is_valid is False
        assert "not an approved security assessment tool" in reason
