# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""The data shapes passed between components.

Why: one agreed shape per step means each component can be tested and
swapped on its own (ingest -> classify -> retrieve -> route -> generate -> validate).
"""
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Ticket:
    """One normalised ticket, whatever channel it arrived on."""
    ticket_id: str
    channel: str              # email | chat | docs_comment | forum | unknown
    text: str                 # subject + body, cleaned, used for classification and retrieval
    original_subject: str     # kept untouched for audit
    original_body: str
    received_at: str
    customer_id: str
    customer_name: str
    customer_tier: str
    customer_region: str
    language_fluency: str
    labels: dict = field(default_factory=dict)   # only used for evaluation, never for decisions
    ingest_warnings: list = field(default_factory=list)


@dataclass
class Classification:
    intent: str
    intent_confidence: float
    urgency: str
    urgency_confidence: float
    alternatives: list        # [{"value": ..., "confidence": ...}] for the next best intents
    answerable_prob: float = 0.0   # chance the docs can solve this specific ticket


@dataclass
class Passage:
    passage_id: str           # e.g. "DOC-AUTH-001#2", resolves to a real piece of the corpus
    doc_id: str
    title: str
    text: str
    score: float


@dataclass
class GuardrailResult:
    name: str
    passed: bool
    details: str = ""


@dataclass
class Outcome:
    """Everything the system decided about one ticket."""
    ticket_id: str
    action: str               # auto_respond | escalate | block
    reason: str               # plain-language reason a support manager can read
    classification: Optional[Classification] = None
    passages: list = field(default_factory=list)
    answer: str = ""
    citations: list = field(default_factory=list)
    guardrails: list = field(default_factory=list)
    escalation_summary: str = ""
    latency_s: float = 0.0
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
