"""Deterministic control policy over evidence supplied by judges."""

from __future__ import annotations

from dataclasses import dataclass

from aap.models import Decision, Judgment, PolicyAction, PolicyDecision


@dataclass(frozen=True)
class PolicyConfig:
    misalignment_threshold: float = 0.90
    unproductive_loop_threshold: float = 0.90


class PolicyEngine:
    """Turn structured evidence into a reproducible agent-control decision."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def decide(self, judgments: list[Judgment]) -> PolicyDecision:
        hard_violations = [
            judgment
            for judgment in judgments
            if judgment.judge == "deterministic" and judgment.decision == Decision.VIOLATION
        ]
        if hard_violations:
            return PolicyDecision(
                action=PolicyAction.INTERRUPT,
                reason=f"deterministic_{hard_violations[0].dimension}",
                judgments=hard_violations,
            )

        for judgment in judgments:
            if judgment.judge != "jev":
                continue
            if (
                judgment.dimension == "unproductive_loop"
                and judgment.decision == Decision.UNPRODUCTIVE
                and judgment.probability >= self.config.unproductive_loop_threshold
            ):
                return PolicyDecision(action=PolicyAction.INTERRUPT, reason="jev_unproductive_loop", judgments=[judgment])
            if (
                judgment.dimension == "goal_alignment"
                and judgment.decision == Decision.MISALIGNED
                and judgment.probability >= self.config.misalignment_threshold
            ):
                return PolicyDecision(action=PolicyAction.WARN, reason="jev_possible_goal_drift", judgments=[judgment])

        warnings = [judgment for judgment in judgments if judgment.severity.value == "warning"]
        if warnings:
            return PolicyDecision(PolicyAction.WARN, "judge_warning", warnings)
        return PolicyDecision(action=PolicyAction.CONTINUE, reason="no_policy_trigger", judgments=judgments)
