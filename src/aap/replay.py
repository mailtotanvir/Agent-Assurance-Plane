"""Persistence and offline replay for reproducible assurance runs."""

from __future__ import annotations

import json
from pathlib import Path

from aap.models import AgentEvent, Judgment, PolicyDecision
from aap.runtime import AssuranceRun
from aap.secrets import redact


def save_run(run: AssuranceRun, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(run.model_dump()), indent=2) + "\n", encoding="utf-8")


def load_run(path: Path) -> AssuranceRun:
    data = json.loads(path.read_text(encoding="utf-8"))
    return AssuranceRun(
        run_id=data["run_id"],
        goal=data["goal"],
        events=[AgentEvent.model_validate(event) for event in data["events"]],
        judgments=[Judgment.model_validate(judgment) for judgment in data["judgments"]],
        policy_decisions=[PolicyDecision.model_validate(decision) for decision in data["policy_decisions"]],
    )
