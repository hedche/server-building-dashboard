"""
Correlation ID (Request ID) context management for request tracing.
Uses contextvars for async-safe request-scoped storage.
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable to hold the correlation ID for the current request
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID, or None if not set."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new UUID-based correlation ID."""
    return str(uuid.uuid4())
