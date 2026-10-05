from security_tools.base import ToolResult
from security_tools.runner import run_hardened_http_request


def check_cookie_attributes(target: str) -> ToolResult:
    """
    Tool 3 — Cookie Security Attributes
    Inspects Set-Cookie response headers for flags:
    - Secure
    - HttpOnly
    - SameSite (Strict / Lax / None)
    """
    response, failure, duration_ms = run_hardened_http_request(target, "cookie_attributes")
    if failure is not None:
        return failure

    cookie_headers = response.headers.get_list("set-cookie")
    observations = []

    for cookie_str in cookie_headers:
        # Split attributes
        parts = [p.strip() for p in cookie_str.split(";") if p.strip()]
        if not parts:
            continue

        cookie_name = parts[0].split("=")[0].strip() if "=" in parts[0] else parts[0]
        # Never store sensitive cookie values!
        cookie_name_sanitized = cookie_name[:50]

        lower_parts = [p.lower() for p in parts]
        attr_keys_lower = {p.split("=")[0].strip() for p in lower_parts}

        samesite_val = None
        for p in lower_parts:
            if p.startswith("samesite="):
                samesite_val = p.split("=", 1)[1].strip()
                break

        observations.append({
            "cookie_name": cookie_name_sanitized,
            "secure": "secure" in attr_keys_lower,
            "httponly": "httponly" in attr_keys_lower,
            "samesite": samesite_val is not None,
            "samesite_value": samesite_val,
        })

    return ToolResult(
        tool_name="cookie_attributes",
        status="completed",
        evidence={
            "cookie_count": len(cookie_headers),
            "cookies": observations,
            "has_insecure_flags": any(
                (not c["secure"] or not c["httponly"] or not c["samesite"])
                for c in observations
            ) if observations else False,
        },
        message=f"Cookie security attributes inspected for {len(cookie_headers)} cookie(s)",
        duration_ms=duration_ms,
    )
