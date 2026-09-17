# Agent Assurance Plane

Agent Assurance Plane (AAP) is a small, local-first runtime assurance layer for tool-using AI agents. It treats an agent run as an event stream, combines deterministic invariants with probabilistic TypeSafe Jev judgments, and makes control decisions through a deterministic policy engine.

> Observability tells you what an AI agent did. Assurance tells you whether it should have.

## What it demonstrates

- Hard guarantees: repeated tools, unsafe mutations, budgets, and invalid transitions.
- Contextual signal: goal alignment, progress, tool appropriateness, and unproductive loops via Jev.
- Clear separation: Jev supplies evidence; the policy engine decides whether to warn or interrupt.
- Reproducible runs: scripted scenarios are serializable and replayable without live API calls.

## Quick start

```bash
uv sync --extra dev
uv run aap demo normal
uv run aap demo loop
uv run aap demo drift
uv run aap evaluate
uv run aap serve
```

Live Jev calls require `TYPESAFE_API_KEY` in the environment. Copy `.env.example` only as a reference; do not commit a `.env` file.

```bash
uv run aap jev-smoke
```

## Architecture

```text
agent events -> state -> deterministic judges + JevJudge -> judgment bus -> policy -> intervention
```

The internal `Judgment` model is provider-neutral. `JevJudge` is the only component aware of the TypeSafe SDK.

The web UI is available at `http://127.0.0.1:8000` after `uv run aap serve`. Turn on **Live Jev evidence** only when you want the demo to make live TypeSafe API calls.

## Replays and evaluation

```bash
uv run aap demo loop --output runs/example-loop.json
uv run aap replay runs/example-loop.json
uv run aap evaluate
```

Replays never call Jev. The evaluation command is intentionally offline and reports expected versus actual deterministic violations, intervention outcomes, and time-to-intervention.

## Safety and privacy

AAP deliberately stores no API keys. It redacts secret-like fields from persisted events and never writes live API credentials to run files or logs. The simulation uses fictional checkout-latency data only.

## Development

```bash
uv run pytest
uv run ruff check .
```

This is a research/demo prototype, not a production authorization system.
