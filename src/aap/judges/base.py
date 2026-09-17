"""Judge interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from aap.models import AgentState, Judgment


class Judge(ABC):
    name: str

    @abstractmethod
    def evaluate(self, state: AgentState) -> list[Judgment]:
        """Evaluate a state without making policy decisions."""
