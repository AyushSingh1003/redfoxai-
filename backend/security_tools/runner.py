import time
from typing import Tuple, Optional
import httpx

from config import settings
from policy.scope import is_target_allowed
from security_tools.base import ToolResult


def run_hardened_http_request(
    target: str,
    tool_name: str,
    timeout_seconds: Optional[float] = None,
) -> Tuple[Optional[httpx.Response], Optional[ToolResult], float]:
    """
    Executes a hardened HTTP GET request against the authorized target.
    Enforces:
    1. Multi-layer scope re-validation before network call.
    2. Strict timeout.
    3. Disabled redirects (follow_redirects=False to prevent SSRF bypass).
    4. Response size limit to prevent resource exhaustion / DoS.
    """
    timeout = timeout_seconds or settings.TOOL_TIMEOUT_SECONDS
    start_time = time.perf_counter()

    # Multi-layer defense: re-check target authorization immediately before execution
    if not is_target_allowed(target):
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return None, ToolResult(
            tool_name=tool_name,
            status="failed",
            evidence={"error": "scope_violation", "target": target},
            message=f"Execution blocked: Target {target} is outside authorized lab scope.",
            duration_ms=duration_ms,
            error="Scope violation",
        ), duration_ms

    try:
        # Use streaming to enforce response size limits safely
        with httpx.Client(follow_redirects=False, timeout=timeout) as client:
            with client.stream("GET", target) as response:
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > settings.MAX_RESPONSE_BYTES:
                        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        return None, ToolResult(
                            tool_name=tool_name,
                            status="failed",
                            evidence={
                                "error": "response_size_exceeded",
                                "max_bytes": settings.MAX_RESPONSE_BYTES,
                            },
                            message=f"Response exceeded size limit ({settings.MAX_RESPONSE_BYTES} bytes)",
                            duration_ms=duration_ms,
                            error="Response size limit exceeded",
                        ), duration_ms

                # Construct a standard response with body loaded
                response.read()
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return response, None, duration_ms

    except httpx.TimeoutException as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return None, ToolResult(
            tool_name=tool_name,
            status="failed",
            evidence={"error": "timeout", "detail": str(e), "timeout_limit": timeout},
            message=f"Request timed out after {timeout}s while reaching {target}",
            duration_ms=duration_ms,
            error=f"Timeout: {e}",
        ), duration_ms

    except httpx.ConnectError as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return None, ToolResult(
            tool_name=tool_name,
            status="failed",
            evidence={"error": "connect_error", "detail": str(e)},
            message=f"Could not connect to {target}",
            duration_ms=duration_ms,
            error=f"Connection error: {e}",
        ), duration_ms

    except httpx.HTTPError as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return None, ToolResult(
            tool_name=tool_name,
            status="failed",
            evidence={"error": type(e).__name__.lower(), "detail": str(e)},
            message=f"HTTP error scanning {target}: {type(e).__name__}",
            duration_ms=duration_ms,
            error=str(e),
        ), duration_ms

    except Exception as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return None, ToolResult(
            tool_name=tool_name,
            status="failed",
            evidence={"error": "unexpected", "detail": f"{type(e).__name__}: {e}"},
            message=f"Unexpected error executing {tool_name}",
            duration_ms=duration_ms,
            error=str(e),
        ), duration_ms
