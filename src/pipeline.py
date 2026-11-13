# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""The whole chain for one ticket:

  ingest -> input guardrail -> classify -> retrieve -> route -> generate -> output guardrails -> log

Every ticket ends in exactly one of: auto_respond, escalate, block.
Nothing raises out of process(): any unexpected error becomes a logged
escalation, so one bad ticket can never stop a run (A9, A11).
"""
import json
import time
import traceback
from pathlib import Path

from src.classify import TicketClassifier
from src.config import get_settings
from src.embeddings import get_embedder
from src.generate import Generator, with_disclosure
from src.guardrails import check_instruction_integrity, validate_answer
from src.ingest import normalise
from src.logging_store import DecisionLog
from src.models import Outcome
from src.retrieve import Retriever, build_passages
from src.route import escalation_summary, pre_generation_route

# Requirement IDs from the PRD, recorded with each decision for traceability.
REQ = {"ingest": ["FR-01"], "classification": ["FR-02"], "retrieval": ["FR-03"],
       "routing": ["FR-04"], "generation": ["FR-05", "FR-09"], "validation": ["FR-06"],
       "final": ["FR-07", "FR-08"]}


class SupportPipeline:
    def __init__(self, run_id: str, settings=None):
        self.s = settings or get_settings()
        self.s.storage_dir.mkdir(parents=True, exist_ok=True)

        passages = build_passages(self.s.docs_path, self.s.chunk_strategy)
        train = [normalise(t) for t in json.loads(Path(self.s.train_path).read_text(encoding="utf-8"))]
        train = [t for t in train if t.text and t.labels.get("intent")]

        # TF-IDF needs to learn its vocabulary; MiniLM ignores this corpus.
        corpus = [p["text"] for p in passages] + [t.text for t in train]
        self.embedder = get_embedder(self.s.embedding_backend, self.s.embedding_model, corpus)
        self.retriever = Retriever(self.s, self.embedder, passages)
        self.classifier = TicketClassifier(self.embedder, [t.text for t in train],
                                           [t.labels["intent"] for t in train],
                                           [t.labels.get("urgency", "medium") for t in train],
                                           [bool(t.labels.get("answerable_from_docs")) for t in train])
        self.generator = Generator(self.s)
        self.log = DecisionLog(self.s.db_path, run_id)
        self.model_label = (self.s.model_name if self.s.llm_provider != "offline" else "offline-extractive")

    def kill_switch_on(self) -> bool:
        return (not self.s.auto_respond_enabled) or self.s.kill_switch_file.exists()

    def process(self, raw) -> tuple:
        """Returns (ticket, outcome). Never raises."""
        start = time.perf_counter()
        ticket = normalise(raw)
        try:
            outcome = self._process(ticket)
        except Exception as exc:                                  # last line of defence
            outcome = Outcome(ticket.ticket_id, "escalate",
                              f"Unexpected system error, handed to an agent: {type(exc).__name__}: {exc}",
                              escalation_summary=traceback.format_exc(limit=3))
        outcome.latency_s = round(time.perf_counter() - start, 3)
        self._log_final(ticket, outcome)
        return ticket, outcome

    def _process(self, ticket) -> Outcome:
        s, log, tid = self.s, self.log, ticket.ticket_id
        summary = ticket.text[:200]

        # 1. Input guardrail: is the customer trying to instruct the system?
        integrity = check_instruction_integrity(ticket.text)
        if not integrity.passed:
            reason = "Ticket contains text that tries to give the system instructions; held for review."
            log.record(tid, "validation", "block", reason, input_summary=summary,
                       guardrails={integrity.name: integrity.details}, requirement_ids=["FR-06"])
            return Outcome(tid, "block", reason, guardrails=[vars(integrity)],
                           escalation_summary=escalation_summary(ticket, None, [], reason))

        # 2. Classify (no model call)
        c = self.classifier.classify(ticket.text)
        log.record(tid, "classification", "classified", f"intent={c.intent}, urgency={c.urgency}, answerable_prob={c.answerable_prob}",
                   input_summary=summary, model=f"logreg+{self.embedder.name}", prediction=c.intent,
                   confidence=c.intent_confidence, alternatives=c.alternatives,
                   requirement_ids=REQ["classification"])

        # 3. Retrieve
        passages = self.retriever.search(ticket.text)
        log.record(tid, "retrieval", "retrieved" if passages else "no_relevant_passage",
                   f"{len(passages)} passage(s) above relevance threshold {s.relevance_threshold}",
                   sources=[{"doc_id": p.passage_id, "score": p.score} for p in passages],
                   threshold=s.relevance_threshold, requirement_ids=REQ["retrieval"])

        # 4. Route
        decision, reason = pre_generation_route(ticket, c, passages, s, self.kill_switch_on())
        log.record(tid, "routing", "escalate" if decision == "escalate" else "draft", reason,
                   prediction=c.intent, confidence=c.intent_confidence,
                   threshold=s.confidence_threshold, requirement_ids=REQ["routing"])
        if decision == "escalate":
            return Outcome(tid, "escalate", reason, classification=c, passages=[vars(p) for p in passages],
                           escalation_summary=escalation_summary(ticket, c, passages, reason))

        # 5. Generate
        draft = self.generator.draft(ticket, passages)
        gen_reason = ("Draft produced." if draft["can_answer"] else
                      f"No answer drafted: {draft['error'] or 'model said the passages do not answer it'}.")
        log.record(tid, "generation", "drafted" if draft["can_answer"] else "no_draft", gen_reason,
                   model=self.model_label, prediction=draft["answer"][:300],
                   sources=[{"doc_id": cid} for cid in draft["citations"]],
                   prompt_version=s.prompt_version, requirement_ids=REQ["generation"])
        if not draft["can_answer"]:
            reason = ("The model provider was unavailable, so the ticket was handed to an agent with context."
                      if draft["error"] and "JSON" not in draft["error"] else
                      "The system could not write an answer it could support from the documentation.")
            return Outcome(tid, "escalate", reason, classification=c, passages=[vars(p) for p in passages],
                           tokens_used=draft["tokens"],
                           escalation_summary=escalation_summary(ticket, c, passages, reason))

        # 6. Output guardrails: every check runs, any failure blocks
        checks = validate_answer(draft["answer"], draft["citations"], passages, s)
        failed = [g for g in checks if not g.passed]
        log.record(tid, "validation", "block" if failed else "pass",
                   "; ".join(f"{g.name}: {g.details}" for g in checks),
                   guardrails={g.name: ("pass" if g.passed else "block") for g in checks},
                   requirement_ids=REQ["validation"])
        if failed:
            reason = "Draft blocked by guardrail(s): " + "; ".join(f"{g.name} ({g.details})" for g in failed)
            return Outcome(tid, "block", reason, classification=c, passages=[vars(p) for p in passages],
                           answer=draft["answer"], citations=draft["citations"],
                           guardrails=[vars(g) for g in checks], tokens_used=draft["tokens"],
                           escalation_summary=escalation_summary(ticket, c, passages, reason))

        return Outcome(tid, "auto_respond",
                       f"Answered automatically: {reason} All guardrails passed.",
                       classification=c, passages=[vars(p) for p in passages],
                       answer=with_disclosure(draft["answer"], draft["citations"]),
                       citations=draft["citations"], guardrails=[vars(g) for g in checks],
                       tokens_used=draft["tokens"])

    def _log_final(self, ticket, outcome):
        c = outcome.classification
        self.log.record(ticket.ticket_id, "final", outcome.action, outcome.reason,
                        input_summary=ticket.text[:200], model=self.model_label,
                        prediction=c.intent if c else "", confidence=c.intent_confidence if c else None,
                        alternatives=c.alternatives if c else [],
                        sources=[{"doc_id": p["passage_id"], "score": p["score"]} for p in outcome.passages],
                        threshold=self.s.confidence_threshold,
                        guardrails={g["name"]: ("pass" if g["passed"] else "block") for g in outcome.guardrails},
                        prompt_version=self.s.prompt_version, requirement_ids=REQ["final"])
