from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field


@dataclass
class ToolResult:
    tool_name: str
    status: str  # "completed" | "failed"
    evidence: Dict[str, Any]
    message: str
    duration_ms: float = 0.0
    error: Optional[str] = None


class ToolInputSchema(BaseModel):
    target: str = Field(..., description="Target URL within authorized lab scope")


class SecurityTool:
    def __init__(
        self,
        name: str,
        description: str,
        execution_func: Callable[[str], ToolResult],
        timeout_seconds: float = 5.0,
    ):
        self.name = name
        self.description = description
        self.execution_func = execution_func
        self.timeout_seconds = timeout_seconds

    def execute(self, target: str) -> ToolResult:
        return self.execution_func(target)
