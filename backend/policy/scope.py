from urllib.parse import urlparse
from config import settings


# Denied host patterns (SSRF & Cloud Metadata protection)
FORBIDDEN_HOSTS = {
    "169.254.169.254",  # AWS/GCP/Azure Instance Metadata Service
    "metadata.google.internal",
    "instance-data",
    "100.100.100.200",  # Alibaba metadata
}


def normalize_target(target: str) -> str:
    """Normalize target URL by stripping trailing slashes and whitespace."""
    if not target:
        return ""
    return target.strip().rstrip("/")


def is_target_allowed(target: str) -> bool:
    """
    Strictly verifies that target matches the configured authorized lab target.
    Fails closed on any ambiguity.
    """
    if not target or not isinstance(target, str):
        return False

    normalized = normalize_target(target)
    
    try:
        parsed = urlparse(normalized)
    except Exception:
        return False

    # Must have scheme and netloc
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    # Block SSRF / metadata hosts
    hostname = (parsed.hostname or "").lower()
    if hostname in FORBIDDEN_HOSTS:
        return False

    # Only permitted lab targets
    allowed = {normalize_target(t) for t in settings.allowed_targets}
    return normalized in allowed


def validate_scope_strict(target: str, authorized: bool) -> tuple[bool, str]:
    """
    Validates both user authorization acknowledgement and target lab boundary.
    Returns (is_valid, error_reason).
    """
    if not authorized:
        return False, "Explicit authorization acknowledgement required. Assessment halted."

    if not is_target_allowed(target):
        return (
            False,
            f"Target '{target}' is outside the authorized local lab boundary ({settings.LAB_TARGET}). "
            "Arbitrary external targets are strictly forbidden by policy.",
        )

    return True, "Target and authorization verified within authorized lab scope."
