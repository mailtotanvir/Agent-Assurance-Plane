from aap.evaluation import evaluate_scripted_trajectories
from aap.replay import load_run, save_run
from aap.runtime import AssuranceRuntime
from aap.scenarios import GOAL, normal


def test_replay_persists_without_secret_values(tmp_path) -> None:
    run = AssuranceRuntime().execute(GOAL, normal(), run_id="replay")
    run.events[0].payload["api_key"] = "should-not-appear"
    path = tmp_path / "run.json"
    save_run(run, path)
    assert "should-not-appear" not in path.read_text()
    assert load_run(path).run_id == "replay"


def test_offline_evaluation_passes() -> None:
    assert evaluate_scripted_trajectories()["passed"] is True
