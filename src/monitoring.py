# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Minimal live monitoring with Prometheus counters.

If prometheus_client is installed, start_metrics_server(8001) exposes
http://localhost:8001/metrics while a run is going. If it is not installed,
everything here quietly does nothing, so monitoring can never break a run.
"""
try:
    from prometheus_client import Counter, Histogram, start_http_server
    TICKETS = Counter("tickets_processed_total", "Tickets processed", ["channel", "action"])
    GUARDRAIL_BLOCKS = Counter("guardrail_blocks_total", "Responses blocked", ["guardrail"])
    LATENCY = Histogram("ticket_seconds", "End-to-end processing time per ticket")
    CONFIDENCE = Histogram("intent_confidence", "Intent confidence (drift shows here first)",
                           buckets=[i / 10 for i in range(11)])
    ENABLED = True
except ImportError:  # pragma: no cover
    ENABLED = False


def start_metrics_server(port: int):
    if ENABLED:
        start_http_server(port)


def observe(outcome, channel: str):
    if not ENABLED:
        return
    TICKETS.labels(channel=channel, action=outcome.action).inc()
    LATENCY.observe(outcome.latency_s)
    if outcome.classification:
        CONFIDENCE.observe(outcome.classification.intent_confidence)
    for g in outcome.guardrails:
        if not g["passed"]:
            GUARDRAIL_BLOCKS.labels(guardrail=g["name"]).inc()
