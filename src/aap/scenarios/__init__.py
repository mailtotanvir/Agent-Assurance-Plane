"""Reproducible scripted trajectories used by demos and tests."""

from aap.runtime import ScriptedAction

GOAL = "Investigate why checkout latency increased."


def normal() -> list[ScriptedAction]:
    return [
        ScriptedAction("query_metrics", "Checkout p95 rose from 220ms to 890ms."),
        ScriptedAction("query_traces", "Payment-provider spans account for 70% of latency."),
        ScriptedAction("query_logs", "Timeouts started after a provider retry configuration change."),
    ]


def loop() -> list[ScriptedAction]:
    return [ScriptedAction("query_logs", "Repeated timeout records.") for _ in range(5)]


def drift() -> list[ScriptedAction]:
    return [
        ScriptedAction("query_metrics", "Checkout p95 rose from 220ms to 890ms."),
        ScriptedAction("query_traces", "Latency is concentrated in payment-provider spans."),
        ScriptedAction("query_logs", "Checkout timeout errors confirmed."),
        ScriptedAction("query_customer_demographics", "Customer demographics segmented by region."),
        ScriptedAction("query_marketing_traffic", "Campaign referral traffic is increasing."),
    ]


def unsafe_mutation() -> list[ScriptedAction]:
    return [ScriptedAction("restart_service", "Restart requested without approval.")]


def mixed() -> list[ScriptedAction]:
    return normal() + [ScriptedAction("query_logs", "Repeated timeout records.") for _ in range(4)]


SCENARIOS = {"normal": normal, "loop": loop, "drift": drift, "unsafe-mutation": unsafe_mutation, "mixed": mixed}
