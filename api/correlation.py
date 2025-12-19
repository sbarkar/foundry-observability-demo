"""
Utilities for generating and managing correlation IDs.
"""
import uuid


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())
