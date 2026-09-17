"""Conservative redaction for values that may enter events or persisted runs."""

from __future__ import annotations

from typing import Any

SENSITIVE_MARKERS = ("api_key", "apikey", "secret", "token", "password", "authorization", "credential")


def redact(value: Any) -> Any:
    """Return a recursively redacted copy; never mutate the live runtime state."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if any(marker in key.lower() for marker in SENSITIVE_MARKERS) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value
