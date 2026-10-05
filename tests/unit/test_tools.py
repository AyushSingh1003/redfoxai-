from unittest.mock import patch, MagicMock
import httpx
import pytest

from security_tools.registry import tool_registry
from security_tools.http_status import check_http_status
from security_tools.security_headers import check_security_headers
from security_tools.cookies import check_cookie_attributes


def test_tool_registry_contains_only_approved():
    tools = tool_registry.list_tools()
    tool_names = {t["name"] for t in tools}
    assert tool_names == {"http_status", "security_headers", "cookie_attributes"}
    assert tool_registry.is_registered("http_status") is True
    assert tool_registry.is_registered("arbitrary_tool") is False


def test_tool_execution_unregistered_fails_safely():
    res = tool_registry.execute_tool("nonexistent_tool", "http://juice-shop:3000")
    assert res.status == "failed"
    assert "not in the authorized tool registry" in res.message


def test_http_status_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
    mock_resp.content = b"<html>Test</html>"
    mock_resp.http_version = "HTTP/1.1"

    with patch("security_tools.http_status.run_hardened_http_request", return_value=(mock_resp, None, 14.5)):
        res = check_http_status("http://juice-shop:3000")
        assert res.status == "completed"
        assert res.evidence["status_code"] == 200
        assert res.evidence["content_type"] == "text/html; charset=utf-8"
        assert res.evidence["content_length_bytes"] == len(b"<html>Test</html>")
        assert res.duration_ms == 14.5


def test_security_headers_inspection():
    mock_resp = MagicMock()
    mock_resp.headers = {
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
    }

    with patch("security_tools.security_headers.run_hardened_http_request", return_value=(mock_resp, None, 20.0)):
        res = check_security_headers("http://juice-shop:3000")
        assert res.status == "completed"
        assert "x-content-type-options" in res.evidence["present_headers"]
        assert "content-security-policy" in res.evidence["missing_headers"]
        assert "strict-transport-security" in res.evidence["missing_headers"]
        assert res.evidence["compliance_ratio"] < 1.0


def test_cookie_attributes_inspection():
    mock_resp = MagicMock()
    # Mock Set-Cookie headers with one secure cookie and one insecure cookie
    mock_resp.headers.get_list.return_value = [
        "session_id=abc1234; Path=/; Secure; HttpOnly; SameSite=Strict",
        "tracking_pref=opt_in; Path=/",
    ]

    with patch("security_tools.cookies.run_hardened_http_request", return_value=(mock_resp, None, 15.0)):
        res = check_cookie_attributes("http://juice-shop:3000")
        assert res.status == "completed"
        assert res.evidence["cookie_count"] == 2
        cookies = res.evidence["cookies"]
        assert cookies[0]["secure"] is True
        assert cookies[0]["httponly"] is True
        assert cookies[0]["samesite"] is True
        assert cookies[0]["samesite_value"] == "strict"
        # Second cookie is insecure
        assert cookies[1]["secure"] is False
        assert cookies[1]["httponly"] is False
        assert cookies[1]["samesite"] is False
        assert res.evidence["has_insecure_flags"] is True
