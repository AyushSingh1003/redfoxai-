from typing import List, Tuple

ALLOWED_TOOLS = {
    "http_status",
    "security_headers",
    "cookie_attributes",
}


def validate_plan_policy(plan: List[str]) -> Tuple[bool, str]:
    """
    Validates that every tool proposed in the plan is pre-approved in the registry.
    Disallows dynamically injected tools or empty plans.
    """
    if not plan or not isinstance(plan, list):
        return False, "Plan must contain at least one approved security check."

    for tool in plan:
        if not isinstance(tool, str):
            return False, f"Invalid tool identifier type: {type(tool)}"
        if tool not in ALLOWED_TOOLS:
            return False, f"Tool '{tool}' is not an approved security assessment tool."

    return True, f"Plan verified. All {len(plan)} tool(s) comply with security policy."
