"""Run scripted agent trajectories through the assurance plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from aap.bus import JudgmentBus
from aap.judges.base import Judge
from aap.judges.deterministic import DeterministicJudge
from aap.models import AgentEvent, AgentState, EventType, Judgment, PolicyAction, PolicyDecision
from aap.policy import PolicyEngine


@dataclass(frozen=True)
class ScriptedAction:
    tool: str
    result: str
    token_cost: int = 100
    environment_updates: dict[str, object] = field(default_factory=dict)


@dataclass
class AssuranceRun:
    run_id: str
    goal: str
    events: list[AgentEvent] = field(default_factory=list)
    judgments: list[Judgment] = field(default_factory=list)
    policy_decisions: list[PolicyDecision] = field(default_factory=list)

    @property
    def final_action(self) -> PolicyAction:
        return self.policy_decisions[-1].action if self.policy_decisions else PolicyAction.CONTINUE

    def model_dump(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "events": [event.model_dump(mode="json") for event in self.events],
            "judgments": [judgment.model_dump(mode="json") for judgment in self.judgments],
            "policy_decisions": [decision.model_dump(mode="json") for decision in self.policy_decisions],
        }


class AssuranceRuntime:
    def __init__(
        self,
        deterministic_judge: Judge | None = None,
        contextual_judge: Judge | None = None,
        policy: PolicyEngine | None = None,
    ) -> None:
        self.deterministic_judge = deterministic_judge or DeterministicJudge()
        self.contextual_judge = contextual_judge
        self.policy = policy or PolicyEngine()

    def execute(self, goal: str, actions: list[ScriptedAction], run_id: str | None = None) -> AssuranceRun:
        run_id = run_id or str(uuid4())
        run = AssuranceRun(run_id=run_id, goal=goal)
        bus = JudgmentBus()
        state = AgentState(run_id=run_id, original_goal=goal)
        run.events.append(AgentEvent(run_id=run_id, step_id=0, event_type=EventType.TASK_STARTED, payload={"goal": goal}))

        for step_id, action in enumerate(actions, start=1):
            state.current_tool = action.tool
            state.current_tool_result = action.result
            state.previous_tools.append(action.tool)
            state.token_cost += action.token_cost
            state.environment.update(action.environment_updates)
            tool_event = AgentEvent(run_id=run_id, step_id=step_id, event_type=EventType.TOOL_CALL, payload={"tool": action.tool})
            result_event = AgentEvent(
                run_id=run_id, step_id=step_id, event_type=EventType.TOOL_RESULT, payload={"tool": action.tool, "result": action.result}
            )
            state.recent_events.extend([tool_event, result_event])
            run.events.extend([tool_event, result_event])

            judgments = self.deterministic_judge.evaluate(state)
            if self.contextual_judge is not None:
                judgments.extend(self.contextual_judge.evaluate(state))
            run.judgments.extend(judgments)
            run.events.extend(bus.emit_many(judgments, run_id, step_id))

            decision = self.policy.decide(judgments)
            run.policy_decisions.append(decision)
            run.events.append(
                AgentEvent(
                    run_id=run_id,
                    step_id=step_id,
                    event_type=EventType.POLICY_DECIDED,
                    payload=decision.model_dump(mode="json"),
                )
            )
            if decision.action == PolicyAction.INTERRUPT:
                state.interrupted = True
                run.events.append(
                    AgentEvent(
                        run_id=run_id,
                        step_id=step_id,
                        event_type=EventType.AGENT_INTERRUPTED,
                        payload={"reason": decision.reason},
                    )
                )
                break
        else:
            run.events.append(AgentEvent(run_id=run_id, step_id=len(actions) + 1, event_type=EventType.TASK_COMPLETED))
        return run
