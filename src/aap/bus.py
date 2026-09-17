"""A tiny in-process event and judgment stream."""

from __future__ import annotations

from collections.abc import Iterable

from aap.models import AgentEvent, EventType, Judgment


class JudgmentBus:
    """Stores first-class judgments and their corresponding event records."""

    def __init__(self) -> None:
        self.judgments: list[Judgment] = []
        self.events: list[AgentEvent] = []

    def emit(self, judgment: Judgment, run_id: str, step_id: int) -> AgentEvent:
        self.judgments.append(judgment)
        event = AgentEvent(
            run_id=run_id,
            step_id=step_id,
            event_type=EventType.JUDGMENT_EMITTED,
            payload=judgment.model_dump(mode="json"),
        )
        self.events.append(event)
        return event

    def emit_many(self, judgments: Iterable[Judgment], run_id: str, step_id: int) -> list[AgentEvent]:
        return [self.emit(judgment, run_id, step_id) for judgment in judgments]
