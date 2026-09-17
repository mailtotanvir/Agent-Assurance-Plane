"""Command line entry points for AAP."""

from __future__ import annotations

import argparse
import json

from aap.judges.jev import JevJudge
from aap.models import AgentState


def main() -> None:
    parser = argparse.ArgumentParser(prog="aap", description="Agent Assurance Plane")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("jev-smoke", help="Make a minimal live Jev judgment call.")
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


if __name__ == "__main__":
    main()
