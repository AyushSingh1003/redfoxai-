# Backward compatibility shim
from security_tools.base import ToolResult
from security_tools.http_status import check_http_status
from security_tools.security_headers import check_security_headers
from security_tools.cookies import check_cookie_attributes
from security_tools.registry import tool_registry

TOOLS = {
    "http_status": check_http_status,
    "security_headers": check_security_headers,
    "cookie_attributes": check_cookie_attributes,
}

__all__ = [
    "ToolResult",
    "check_http_status",
    "check_security_headers",
    "check_cookie_attributes",
    "tool_registry",
    "TOOLS",
]
