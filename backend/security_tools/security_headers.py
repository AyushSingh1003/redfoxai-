from security_tools.base import ToolResult
from security_tools.runner import run_hardened_http_request

SECURITY_HEADERS_OF_INTEREST = [
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
]


def check_security_headers(target: str) -> ToolResult:
    """
    Tool 2 — Security Headers Inspection
    Inspects selected security-related HTTP response headers.
    Returns observations of present vs missing headers.
    """
    response, failure, duration_ms = run_hardened_http_request(target, "security_headers")
    if failure is not None:
        return failure

    present = {}
    missing = []

    for header in SECURITY_HEADERS_OF_INTEREST:
        val = response.headers.get(header)
        if val:
            # Mask or truncate any excessively long header to protect database/logs
            present[header] = val[:500] if len(val) > 500 else val
        else:
            missing.append(header)

    return ToolResult(
        tool_name="security_headers",
        status="completed",
        evidence={
            "present_headers": present,
            "missing_headers": missing,
            "total_evaluated": len(SECURITY_HEADERS_OF_INTEREST),
            "compliance_ratio": round(len(present) / len(SECURITY_HEADERS_OF_INTEREST), 2),
        },
        message=f"Security headers inspected: {len(present)} present, {len(missing)} missing",
        duration_ms=duration_ms,
    )
