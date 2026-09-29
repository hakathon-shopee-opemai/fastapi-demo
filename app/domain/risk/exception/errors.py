"""Domain-level errors for the risk context."""
from __future__ import annotations


class InvalidSnapshotError(Exception):
    """Raised when an order snapshot cannot be scored."""
