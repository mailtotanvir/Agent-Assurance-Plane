# Agent Assurance Plane

> Observability tells you what an AI agent did.<br>
> **Agentic Assurance tells you whether it should have.**

Agent Assurance Plane (AAP) is a small, local-first runtime assurance layer for tool-using AI agents. It keeps **execution**, **judgment**, and **control** separate:

    Execution agent → event stream → Agentic Assurance → deterministic policy → continue / warn / interrupt

The execution agent does work. Agentic Assurance independently observes its bounded state, applies hard safeguards and contextual assessment, and supplies structured evidence. The policy engine—not a model—owns the final control decision.

## Why this exists

Most agent systems can tell you which tools ran. That is useful, but it does not tell an operator whether the agent is still advancing the requested goal, repeating itself, or approaching an unsafe action.

AAP explores the boundary:

| Hard safeguards | Agentic Assurance |
| --- | --- |
| Known rules with known outcomes | Context-sensitive, probabilistic evidence |
| Repeated tool calls | Goal alignment |
| Unapproved production mutations | Progress |
| Budget and forbidden-transition checks | Tool appropriateness and unproductive loops |
| Interrupt on violation | Inform a deterministic policy threshold |

The UI shows both signals side by side. It intentionally does not hide disagreement behind a single score.

## Demo scenarios

| Scenario | What it proves | Expected policy outcome |
| --- | --- | --- |
| `normal` | Focused investigation remains within safeguards | Continue |
| `loop` | A hard repetition rule catches an unproductive loop | Interrupt |
| `drift` | Context can identify behavior that rules alone may miss | Continue or warn in live assurance mode |
| `unsafe-mutation` | Production-affecting tools require approval | Interrupt |
| `forbidden-transition` | Impossible environment changes are blocked | Interrupt |
| `mixed` | Productive work can later become a deterministic loop | Interrupt |

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run aap serve --port 8010
```

Open [http://127.0.0.1:8010](http://127.0.0.1:8010). Choose a scenario and run it. The page first shows the process, then an outcome, then a step-by-step comparison of hard safeguards and Agentic Assurance.

Run scenarios from the terminal:

```bash
uv run aap demo normal
uv run aap demo loop
uv run aap demo mixed
uv run aap evaluate
```

## Live Agentic Assurance

The contextual layer uses TypeSafe Jev through a narrow adapter. It is optional: scripted demos, replay, and evaluation work offline.

```bash
export TYPESAFE_API_KEY=...
uv run aap jev-smoke
uv run aap demo drift --live-jev
```

The UI labels this signal **Agentic Assurance**. The TypeSafe-specific SDK is isolated to `src/aap/judges/jev.py`; the rest of the application operates on provider-neutral `Judgment` objects.

## Architecture

```text
Execution agent
      │
      ▼
  Agent events ──► Agent state
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
  Hard safeguards              Agentic Assurance
  deterministic rules          bounded contextual evaluation
          │                           │
          └─────────────┬─────────────┘
                        ▼
                  Judgment bus
                        ▼
             Deterministic policy engine
                        ▼
             CONTINUE / WARN / INTERRUPT
```

### Hard safeguards

- Excessive consecutive use of the same tool
- Unapproved `restart_service`, `change_config`, or `deploy`
- Simulated token/cost budget breach
- Forbidden simulated state transition

### Agentic Assurance dimensions

- Goal alignment
- Progress
- Tool appropriateness
- Unproductive loop

## Replay and evaluation

Every completed run can be persisted as JSON. Replays do not make API calls.

```bash
uv run aap demo loop --output runs/example-loop.json
uv run aap replay runs/example-loop.json
uv run aap evaluate
```

The offline evaluation suite checks all six scripted trajectories for expected violations, interventions, and time-to-intervention.

## Safety and privacy

- API credentials are read only from environment variables.
- .env and generated run files are ignored by Git.
- Secret-like keys are redacted before run persistence or API responses.
- The sample environment and incident data are fictional.
- This is a research/demo prototype, not a production authorization system.

## Development

```bash
uv run pytest
uv run ruff check .
```

Read the publication draft in [BLOG_POST_DRAFT.md](BLOG_POST_DRAFT.md).

## License

[MIT](LICENSE)
