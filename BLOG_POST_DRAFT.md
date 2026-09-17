# The Agent That Needed an Assurance Plane

*Draft for review. September 2026.*

An agent can leave a beautiful activity log and still be doing the wrong thing.

That is the uncomfortable gap behind most agent demos. We can watch tool calls, inspect prompts, count tokens, replay traces, and admire a fluent final answer. Those are useful forms of observability. But they do not answer the question that matters once an agent can investigate incidents, alter configuration, or consume a meaningful budget:

> Given what the agent has done so far, should it be allowed to take the next action?

I built Agent Assurance Plane around that question. It is a small, local-first runtime layer for tool-using AI agents. One component executes work. A separate component—**Agentic Assurance**—observes the event stream, evaluates both hard safeguards and contextual evidence, and gives a deterministic policy engine the information it needs to continue, warn, or interrupt.

The point is not to build another generic observability dashboard. It is to make agent control understandable and defensible.

## The separation that changes the design

The execution agent and Agentic Assurance are not the same agent.

    Execution agent
        │ emits actions and results
        ▼
    Agentic Assurance
        │ evaluates hard safeguards + contextual evidence
        ▼
    Deterministic policy
        │ continue / warn / interrupt
        ▼
    Execution control

The execution agent investigates a fictional checkout-latency incident using simple tools: metrics, traces, logs, and a few deliberately dangerous production actions. It does not decide whether it is safe. Agentic Assurance independently receives a bounded representation of the agent’s goal, recent actions, results, tool history, and simulated environment state.

That separation is more than a clean diagram. An execution agent is optimized to complete a task. It has little reason to stop and ask whether it has drifted away from the task, repeated an unproductive action, or crossed a boundary that should require human approval. If it is allowed to grade itself, the system’s incentives are badly aligned.

## Two kinds of evidence

The prototype puts two different kinds of signal side by side instead of flattening them into one “agent quality” score.

| Hard safeguards | Agentic Assurance |
| --- | --- |
| Has the agent repeated the same tool too many times? | Is the agent still making progress? |
| Did it attempt a production mutation without approval? | Are its actions still aligned with the original goal? |
| Did it exceed a simulated budget? | Is the current tool appropriate? |
| Did it make a forbidden state transition? | Does the recent trajectory look unproductively repetitive? |
| **Known rule → known outcome** | **Bounded context → calibrated evidence** |

Hard safeguards are deterministic. If a tool repeats beyond the configured limit, the result is a violation. If an agent tries to restart a service without approval, the result is a violation. Those are the system’s non-negotiable guarantees.

But rules alone are not enough. Consider an agent assigned to investigate checkout latency. It correctly starts with metrics, traces, and logs. Then it begins investigating customer demographics, marketing traffic, and unrelated service configuration. Each individual action can be valid. A simple rule engine has no obvious reason to fire.

This is where Agentic Assurance adds signal. The contextual layer evaluates constrained choices for goal alignment, progress, tool appropriateness, and unproductive looping. In the prototype, TypeSafe’s Jev provides this probabilistic evidence behind a narrow adapter. The rest of the system only sees typed, provider-neutral judgments.

> A passing hard safeguard does not prove that the agent is doing useful work. It only proves that the agent has not broken that safeguard.

## Probability informs. Policy controls.

The contextual layer can return a high-confidence judgment that a trajectory appears misaligned. It should not, by itself, get unilateral authority to stop an incident response or block a workflow.

Agent Assurance Plane keeps the final decision deterministic:

| Evidence | Policy response |
| --- | --- |
| Any hard safeguard violation | Interrupt immediately |
| High-confidence unproductive loop | Interrupt at a configured threshold |
| High-confidence goal drift | Warn or intervene at a configured threshold |
| No configured trigger | Continue and retain the evidence |

The model supplies evidence. The policy engine owns control.

That makes the system reviewable. When someone asks why an agent was interrupted, the answer is not “the model felt uncertain.” The answer is that a specific policy consumed named judgments, crossed a configured threshold, and produced a recorded decision.

## A demo that preserves disagreement

The prototype includes reproducible scenarios for normal behavior, deterministic loops, contextual goal drift, unsafe mutations, forbidden transitions, and mixed behavior. Each run is serializable to JSON and can be replayed without making live contextual calls.

The most useful scenario is the one where the two layers do *not* say the same thing.

In a deterministic loop, repeated log queries eventually cause a hard interrupt. Contextual evidence may also suspect an unproductive loop, but the deterministic safeguard is sufficient to act.

In contextual goal drift, hard safeguards can remain green while Agentic Assurance raises a concern. The interface intentionally shows this side by side. It does not hide disagreement behind an averaged score.

That is the research question behind the project:

> What can deterministic observability guarantee, and what additional signal does probabilistic judgment provide?

The answer is not that one replaces the other. The useful system is the composition.

## The product wedge

The first users are teams already carrying the operational cost of autonomous work:

| Team | Risk today | What assurance adds |
| --- | --- | --- |
| SRE and platform teams | A diagnostic loop silently repeats while an incident waits | Hard loop detection plus an auditable interruption reason |
| Agent platform teams | Every new agent reinvents safety logic | A shared event, judgment, and policy contract |
| Engineering leaders | “It worked” is difficult to inspect afterward | Replayable runs and separate evidence for rules and contextual assessment |
| Regulated operators | A model becomes the de facto decision maker | Human-owned thresholds and deterministic enforcement |

The product is not an enormous control plane. The wedge is assurance at the point of action: enough context to evaluate an agent’s trajectory, a clear policy that can intervene, and a timeline a human can understand in seconds.

## What the prototype deliberately does not do

This is a research-quality v0, not a production authorization system. It uses a local process, JSON persistence, scripted trajectories, explicit policies, and a small FastAPI interface. It does not introduce a database, Kafka, Kubernetes, authentication, or cloud infrastructure just to make the demo look larger.

Those omissions are intentional. Before scaling the infrastructure, I wanted to prove the control model:

1. An execution agent produces an event stream.
2. Hard safeguards and Agentic Assurance evaluate the same state independently.
3. A deterministic policy decides whether execution continues.
4. The resulting evidence remains replayable and legible to a human.

## The lesson

An agent is not trustworthy because we can replay what it did.

It becomes governable when execution, judgment, and control are separate—and when every intervention leaves receipts a human can understand.

The ambition of Agent Assurance Plane is modest but important: let rules do the job rules can defend; let probabilistic judgment add context where rules are blind; and never confuse evidence with authority.
