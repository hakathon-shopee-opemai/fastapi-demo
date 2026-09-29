"""Unit tests for CancelAssessmentService against a fake repository."""
from __future__ import annotations

import pytest

from app.application.risk.usecase.saga import CancelAssessmentService


class FakeRepo:
    def __init__(self, existing_order_ids: set[str]) -> None:
        self._ids = set(existing_order_ids)
        self.cancelled: set[str] = set()

    async def mark_cancelled(self, order_id: str) -> str:
        if order_id in self._ids:
            self.cancelled.add(order_id)
            return "CANCELLED"
        return "NO_ASSESSMENT"


@pytest.mark.asyncio
async def test_cancel_existing_assessment():
    repo = FakeRepo({"o-1"})
    assert await CancelAssessmentService(repo).cancel("o-1") == "CANCELLED"
    assert "o-1" in repo.cancelled


@pytest.mark.asyncio
async def test_cancel_absent_assessment_is_noop():
    repo = FakeRepo(set())
    assert await CancelAssessmentService(repo).cancel("o-x") == "NO_ASSESSMENT"
