"""Provider-neutral domain models for an assurance run."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer


def utc_now() -> datetime:
    return datetime.now(UTC)


class EventType(StrEnum):
    TASK_STARTED = "TASK_STARTED"
    LLM_CALL = "LLM_CALL"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    STATE_CHANGE = "STATE_CHANGE"
    LLM_RESPONSE = "LLM_RESPONSE"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    AGENT_INTERRUPTED = "AGENT_INTERRUPTED"
    JUDGMENT_EMITTED = "JUDGMENT_EMITTED"
    POLICY_DECIDED = "POLICY_DECIDED"


class Decision(StrEnum):
    PASS = "pass"
    WARN = "warn"
    VIOLATION = "violation"
    ALIGNED = "aligned"
    UNCERTAIN = "uncertain"
    MISALIGNED = "misaligned"
    PRODUCTIVE = "productive"
    UNPRODUCTIVE = "unproductive"
    APPROPRIATE = "appropriate"
    INAPPROPRIATE = "inappropriate"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PolicyAction(StrEnum):
    CONTINUE = "continue"
    WARN = "warn"
    INTERRUPT = "interrupt"


class AgentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    run_id: str
    step_id: int
    event_type: EventType
    agent_id: str = "demo-agent"
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("timestamp")
    def serialize_timestamp(self, timestamp: datetime) -> str:
        return timestamp.isoformat()


class Judgment(BaseModel):
    judgment_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    judge: str
    dimension: str
    decision: Decision
    probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)
    severity: Severity = Severity.INFO
    probabilities: dict[str, float] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    action: PolicyAction
    reason: str
    judgments: list[Judgment] = Field(default_factory=list)


class AgentState(BaseModel):
    run_id: str
    original_goal: str
    recent_events: list[AgentEvent] = Field(default_factory=list)
    current_tool: str | None = None
    current_tool_result: str | None = None
    previous_tools: list[str] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    token_cost: int = 0
    interrupted: bool = False

    def bounded_context(self, limit: int = 12) -> dict[str, Any]:
        """Return a compact, API-safe representation of the current agent state."""
        return {
            "original_goal": self.original_goal,
            "current_tool": self.current_tool,
            "current_tool_result": self.current_tool_result,
            "previous_tools": self.previous_tools[-limit:],
            "recent_events": [
                {"type": event.event_type, "payload": event.payload} for event in self.recent_events[-limit:]
            ],
            "environment": self.environment,
        }
