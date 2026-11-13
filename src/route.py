# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Route: decide whether a ticket may be answered automatically (A5).

Rules are checked in a fixed order and use no randomness, so the same input
always produces the same decision. Every branch returns a reason written for
a support manager, not an engineer.
"""
from src.config import NEVER_AUTO_INTENTS


def pre_generation_route(ticket, classification, passages, settings, kill_switch_on: bool):
    """Return ("escalate", reason) if the ticket must go to a human,
    or ("proceed", reason) if it may be drafted automatically."""
    if kill_switch_on:
        return "escalate", "Automatic answers are switched off (kill switch); every ticket goes to an agent."
    if "empty ticket" in ticket.ingest_warnings or not ticket.text:
        return "escalate", "The ticket has no readable content, so an agent needs to look at it."
    if classification is None or classification.intent_confidence is None:
        return "escalate", "No confidence score was produced; a missing score is never treated as a high one."
    if classification.intent in NEVER_AUTO_INTENTS:
        return "escalate", (f"Topic '{classification.intent}' is on the never-automate list "
                            "(security, compliance, feature requests, unclear requests).")
    if classification.intent_confidence < settings.confidence_threshold:
        alt = ", ".join(a["value"] for a in classification.alternatives[:2])
        return "escalate", (f"Not confident about the topic ({classification.intent_confidence:.0%} for "
                            f"'{classification.intent}', below the {settings.confidence_threshold:.0%} bar). "
                            f"Other possibilities: {alt}.")
    if not passages:
        return "escalate", ("No documentation passage was relevant enough to ground an answer, "
                            "so the system will not guess.")
    return "proceed", (f"Topic '{classification.intent}' at {classification.intent_confidence:.0%} confidence, "
                       f"with {len(passages)} relevant documentation passage(s).")


def escalation_summary(ticket, classification, passages, reason: str) -> str:
    """The context package an agent receives (Daniel: 'show its working')."""
    lines = [f"Ticket {ticket.ticket_id} via {ticket.channel} ({ticket.customer_tier} customer).",
             f"Why escalated: {reason}"]
    if classification:
        lines.append(f"Likely topic: {classification.intent} ({classification.intent_confidence:.0%}); "
                     f"urgency: {classification.urgency}.")
        if classification.alternatives:
            lines.append("Also possible: " + ", ".join(
                f"{a['value']} ({a['confidence']:.0%})" for a in classification.alternatives if "value" in a))
    if passages:
        lines.append("Documentation that looked relevant: " + "; ".join(
            f"{p.doc_id} '{p.title}' (score {p.score:.2f})" for p in passages))
    else:
        lines.append("No relevant documentation was found.")
    return "\n".join(lines)
