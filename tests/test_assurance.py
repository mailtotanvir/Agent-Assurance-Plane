from aap.runtime import AssuranceRuntime
from aap.scenarios import GOAL, loop, unsafe_mutation


def test_loop_is_interrupted_by_deterministic_rule() -> None:
    run = AssuranceRuntime().execute(GOAL, loop(), run_id="loop")
    assert run.final_action == "interrupt"
    assert any(j.dimension == "tool_repetition" and j.decision == "violation" for j in run.judgments)


def test_unsafe_mutation_is_interrupted() -> None:
    run = AssuranceRuntime().execute(GOAL, unsafe_mutation(), run_id="unsafe")
    assert run.final_action == "interrupt"
    assert run.policy_decisions[-1].reason == "deterministic_production_mutation"
