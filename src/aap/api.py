"""Local FastAPI surface for the assurance timeline demo."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from aap.judges.jev import JevJudge
from aap.runtime import AssuranceRun, AssuranceRuntime
from aap.scenarios import GOAL, SCENARIOS
from aap.secrets import redact

WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
SCENARIO_DESCRIPTIONS = {
    "normal": "A focused checkout-latency investigation that should complete normally.",
    "loop": "The agent repeats the same log query until the hard repetition safeguard interrupts it.",
    "drift": "The agent starts correctly, then turns toward unrelated customer and marketing questions.",
    "unsafe-mutation": "The agent attempts a production-affecting action without approval.",
    "forbidden-transition": "The simulated agent attempts an impossible state change.",
    "mixed": "The agent begins productively but later falls into a repeated-tool loop.",
}


def run_summary(run: AssuranceRun) -> dict[str, object]:
    dimensions: dict[str, list[float]] = {}
    for judgment in run.judgments:
        if judgment.judge == "jev":
            dimensions.setdefault(judgment.dimension, []).append(judgment.probability)
    return {
        "run_id": run.run_id,
        "goal": run.goal,
        "events": len(run.events),
        "deterministic_violations": sum(
            judgment.judge == "deterministic" and judgment.decision.value == "violation" for judgment in run.judgments
        ),
        "jev_warnings": sum(judgment.judge == "jev" and judgment.severity.value == "warning" for judgment in run.judgments),
        "interventions": sum(event.event_type.value == "AGENT_INTERRUPTED" for event in run.events),
        "final_policy": run.final_action,
        "dimension_trajectory": dimensions,
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Assurance Plane", version="0.1.0")
    runs: dict[str, AssuranceRun] = {}

    @app.get("/api/scenarios")
    def scenarios() -> dict[str, object]:
        return {
            "goal": GOAL,
            "scenarios": [
                {"id": name, "description": SCENARIO_DESCRIPTIONS[name]} for name in sorted(SCENARIOS)
            ],
        }

    @app.post("/api/demo/{scenario}")
    def demo(scenario: str, live_jev: bool = False) -> dict[str, object]:
        factory = SCENARIOS.get(scenario)
        if factory is None:
            raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario}")
        runtime = AssuranceRuntime(contextual_judge=JevJudge() if live_jev else None)
        run = runtime.execute(GOAL, factory())
        runs[run.run_id] = run
        return {"run": redact(run.model_dump()), "summary": run_summary(run)}

    @app.get("/api/runs")
    def list_runs() -> list[dict[str, object]]:
        return [run_summary(run) for run in runs.values()]

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, object]:
        run = runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return {"run": redact(run.model_dump()), "summary": run_summary(run)}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    app.mount("/web", StaticFiles(directory=WEB_ROOT), name="web")
    return app


app = create_app()
