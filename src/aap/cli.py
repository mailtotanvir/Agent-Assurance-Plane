"""Command line entry points for AAP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aap.judges.jev import JevJudge
from aap.models import AgentState
from aap.replay import load_run, save_run
from aap.runtime import AssuranceRuntime
from aap.scenarios import GOAL, SCENARIOS


def main() -> None:
    parser = argparse.ArgumentParser(prog="aap", description="Agent Assurance Plane")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("jev-smoke", help="Make a minimal live Jev judgment call.")
    demo_parser = subparsers.add_parser("demo", help="Run a scripted assurance scenario.")
    demo_parser.add_argument("scenario", choices=sorted(SCENARIOS))
    demo_parser.add_argument("--live-jev", action="store_true", help="Evaluate each step with Jev (uses API calls).")
    demo_parser.add_argument("--output", type=Path, help="Write the complete run to JSON.")
    replay_parser = subparsers.add_parser("replay", help="Display a recorded run without API calls.")
    replay_parser.add_argument("run_file", type=Path)
    serve_parser = subparsers.add_parser("serve", help="Start the local assurance timeline web app.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "jev-smoke":
        state = AgentState(
            run_id="jev-smoke",
            original_goal="Investigate why checkout latency increased.",
            current_tool="query_metrics",
            previous_tools=["query_metrics"],
            current_tool_result="Checkout p95 latency increased from 220ms to 890ms.",
            environment={"service": "checkout", "incident": "fictional demo"},
        )
        judgments = JevJudge().evaluate(state)
        print(json.dumps([judgment.model_dump(mode="json") for judgment in judgments], indent=2))
    elif args.command == "demo":
        contextual_judge = JevJudge() if args.live_jev else None
        run = AssuranceRuntime(contextual_judge=contextual_judge).execute(GOAL, SCENARIOS[args.scenario]())
        if args.output:
            save_run(run, args.output)
        _print_run(run.model_dump())
    elif args.command == "replay":
        _print_run(load_run(args.run_file).model_dump())
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("aap.api:app", host=args.host, port=args.port, reload=False)


def _print_run(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, default=str))


if __name__ == "__main__":
    main()
