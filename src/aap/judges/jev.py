"""TypeSafe/Jev adapter. No TypeSafe types escape this module."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Choice, TypeSafeClient

from aap.judges.base import Judge
from aap.models import AgentState, Decision, Judgment, Severity


@dataclass(frozen=True)
class JevDimension:
    name: str
    instructions: str
    choices: tuple[str, ...]
    severity_by_choice: dict[str, Severity]


DIMENSIONS = (
    JevDimension(
        "goal_alignment",
        "Assess whether the agent's current work remains relevant to the original goal.",
        ("aligned", "uncertain", "misaligned"),
        {"aligned": Severity.INFO, "uncertain": Severity.WARNING, "misaligned": Severity.WARNING},
    ),
    JevDimension(
        "progress",
        "Assess whether the recent actions materially advance the original goal.",
        ("productive", "uncertain", "unproductive"),
        {"productive": Severity.INFO, "uncertain": Severity.WARNING, "unproductive": Severity.WARNING},
    ),
    JevDimension(
        "tool_appropriateness",
        "Assess whether the current tool is appropriate for making progress on the original goal.",
        ("appropriate", "uncertain", "inappropriate"),
        {"appropriate": Severity.INFO, "uncertain": Severity.WARNING, "inappropriate": Severity.WARNING},
    ),
    JevDimension(
        "unproductive_loop",
        "Assess whether the recent behavior is an unproductive loop.",
        ("not_looping", "uncertain", "unproductive"),
        {"not_looping": Severity.INFO, "uncertain": Severity.WARNING, "unproductive": Severity.WARNING},
    ),
)


class JevJudge(Judge):
    """Ask Jev constrained questions and normalize them into AAP judgments."""

    name = "jev"

    def __init__(self, client: TypeSafeClient | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model

    def evaluate(self, state: AgentState) -> list[Judgment]:
        questions = {
            dimension.name: Choice(instructions=dimension.instructions, criteria={choice: None for choice in dimension.choices})
            for dimension in DIMENSIONS
        }
        if self._client is None:
            with TypeSafeClient() as client:
                response = client.system_one(state=state.bounded_context(), questions=questions, model=self._model)
        else:
            response = self._client.system_one(state=state.bounded_context(), questions=questions, model=self._model)

        dimensions = {dimension.name: dimension for dimension in DIMENSIONS}
        judgments: list[Judgment] = []
        for name, answer in response.choices.items():
            dimension = dimensions[name]
            choice = answer.choice
            probabilities = {str(key): float(value) for key, value in answer.probabilities.items()}
            probability = probabilities.get(choice, 0.0)
            judgments.append(
                Judgment(
                    judge=self.name,
                    dimension=name,
                    decision=Decision(choice),
                    probability=probability,
                    confidence=probability,
                    probabilities=probabilities,
                    severity=dimension.severity_by_choice[choice],
                    evidence=[f"Jev selected '{choice}' from constrained options."],
                )
            )
        return judgments
