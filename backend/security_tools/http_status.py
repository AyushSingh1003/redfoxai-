from security_tools.base import ToolResult
from security_tools.runner import run_hardened_http_request


def check_http_status(target: str) -> ToolResult:
    """
    Tool 1 — HTTP Status
    Collects:
    - HTTP status code
    - Content-Type header
    - Response timing (latency in ms)
    - Response body size in bytes
    """
    response, failure, duration_ms = run_hardened_http_request(target, "http_status")
    if failure is not None:
        return failure

    content_length = len(response.content) if hasattr(response, "content") else 0
    content_type = response.headers.get("content-type", "unknown")

    return ToolResult(
        tool_name="http_status",
        status="completed",
        evidence={
            "status_code": response.status_code,
            "content_type": content_type,
            "latency_ms": duration_ms,
            "content_length_bytes": content_length,
            "http_version": response.http_version if hasattr(response, "http_version") else "HTTP/1.1",
        },
        message=f"HTTP status {response.status_code} received ({duration_ms}ms, {content_length} bytes)",
        duration_ms=duration_ms,
    )
