from aap.models import AgentState, EventType


def test_bounded_context_limits_event_history() -> None:
    state = AgentState(run_id="run", original_goal="goal")
    assert state.bounded_context()["original_goal"] == "goal"
    assert EventType.TOOL_CALL == "TOOL_CALL"
