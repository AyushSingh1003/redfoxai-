from typing import Dict, List, Optional
from security_tools.base import SecurityTool, ToolResult
from security_tools.http_status import check_http_status
from security_tools.security_headers import check_security_headers
from security_tools.cookies import check_cookie_attributes


class ToolRegistry:
    """
    Strict, immutable registry of authorized deterministic security tools.
    The agent/LLM is strictly forbidden from creating or executing arbitrary tools.
    """

    def __init__(self):
        self._tools: Dict[str, SecurityTool] = {
            "http_status": SecurityTool(
                name="http_status",
                description="Checks HTTP baseline status code, Content-Type, latency, and response size.",
                execution_func=check_http_status,
                timeout_seconds=5.0,
            ),
            "security_headers": SecurityTool(
                name="security_headers",
                description="Inspects presence of critical defensive HTTP response headers (CSP, HSTS, X-Content-Type-Options, etc.).",
                execution_func=check_security_headers,
                timeout_seconds=5.0,
            ),
            "cookie_attributes": SecurityTool(
                name="cookie_attributes",
                description="Inspects Set-Cookie headers for Secure, HttpOnly, and SameSite defensive attributes.",
                execution_func=check_cookie_attributes,
                timeout_seconds=5.0,
            ),
        }

    def get_tool(self, name: str) -> Optional[SecurityTool]:
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "timeout_seconds": tool.timeout_seconds,
            }
            for tool in self._tools.values()
        ]

    def execute_tool(self, name: str, target: str) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                status="failed",
                evidence={"error": "unregistered_tool"},
                message=f"Tool '{name}' is not in the authorized tool registry.",
                error="Tool not registered",
            )
        return tool.execute(target)


# Global singleton registry
tool_registry = ToolRegistry()
