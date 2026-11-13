# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Guardrails: checks that can BLOCK a response (A7).

They run on every ticket in every run, never behind a flag. Each check records
what it looked at and what it found, whether or not it blocked.

- instruction_integrity: runs on the INCOMING ticket (prompt injection)
- private_data, grounding, tone_scope: run on the OUTGOING answer
"""
import re

from src.models import GuardrailResult

# ---------------------------------------------------------------- input check
_INJECTION = re.compile(
    r"(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier|system)?\s*"
    r"(instructions|rules|prompt|guidelines)"
    r"|you are now|act as (an?|the) |pretend to be|developer mode|jailbreak"
    r"|(reveal|show|print|repeat)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)"
    r"|new instructions\s*:|</?\s*(system|ticket|passages?)\s*>",
    re.IGNORECASE)


def check_instruction_integrity(ticket_text: str) -> GuardrailResult:
    m = _INJECTION.search(ticket_text or "")
    if m:
        return GuardrailResult("instruction_integrity", False,
                               f"ticket contains instruction-like text: '{m.group(0)[:60]}'")
    return GuardrailResult("instruction_integrity", True, "no instruction-like text found")


# ------------------------------------------------------------- output checks
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\w)(\+?\d[\d\s().-]{8,}\d)(?!\w)")
_SECRET = re.compile(r"\b(gsk_|sk-|sk_live_|AKIA|ghp_|xox[bp]-)[A-Za-z0-9_\-]{8,}|\b[A-Za-z0-9]{32,}\b")
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return len(digits) >= 13 and total % 10 == 0


def check_private_data(answer: str) -> GuardrailResult:
    found = []
    if _EMAIL.search(answer):
        found.append("email address")
    if _SECRET.search(answer):
        found.append("key or token")
    if any(_luhn_ok(m.group(0)) for m in _CARD.finditer(answer)):
        found.append("card-like number")
    elif _PHONE.search(answer):
        found.append("phone-like number")
    if found:
        return GuardrailResult("private_data", False, "found: " + ", ".join(found))
    return GuardrailResult("private_data", True, "no email, phone, key or card number found")


_STOP = set("""a an the and or but if then than that this these those to of in on for with from by at as is are
was were be been it its your you we our they their can will would should could may might must not no do does
did have has had there here what which who when where why how all any each more most other some such only own
same so too very just also into out about over after before again further once please""".split())


def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z0-9_-]+", text.lower()) if len(w) > 3 and w not in _STOP}


def check_grounding(answer: str, citations: list, passages: list, min_overlap: float) -> GuardrailResult:
    retrieved = {p.passage_id: p for p in passages}
    if not citations:
        return GuardrailResult("grounding", False, "answer has no citations")
    invented = [c for c in citations if c not in retrieved]
    if invented:
        return GuardrailResult("grounding", False, f"cites passages that were not retrieved: {invented}")
    source_words = set().union(*(_content_words(retrieved[c].text) for c in citations))
    answer_words = _content_words(answer)
    if not answer_words:
        return GuardrailResult("grounding", False, "answer has no checkable content")
    overlap = len(answer_words & source_words) / len(answer_words)
    unsupported = sorted(answer_words - source_words)[:8]
    if overlap < min_overlap:
        return GuardrailResult("grounding", False,
                               f"only {overlap:.0%} of answer words appear in cited passages; "
                               f"unsupported words: {unsupported}")
    return GuardrailResult("grounding", True, f"{overlap:.0%} of answer words found in cited passages")


# Blocks the system PROMISING money or timelines. Explaining a documented policy
# ("credits are applied to the next invoice rather than refunded") is allowed.
_COMMITMENT = re.compile(
    r"\b(we('ve| have| will|'ll)? (issued|processed|applied|refunded|credited|refund|credit)\b"
    r"|refund (has been|was|will be) (issued|processed|approved)|(issue|process|approve) (a|your) refund"
    r"|discount|compensat\w+|reimburs\w+|free of charge"
    r"|we will (fix|resolve|deploy|release) (this|it) (by|within)|within \d+ (hours?|days?)"
    r"|guarantee\w*|we promise)\b"
    r"|(send|share|provide|tell) (us|me) your (password|api key|secret|token)",
    re.IGNORECASE)


def check_tone_scope(answer: str) -> GuardrailResult:
    m = _COMMITMENT.search(answer)
    if m:
        return GuardrailResult("tone_scope", False,
                               f"makes a commitment the system may not make: '{m.group(0)}'")
    return GuardrailResult("tone_scope", True, "no refunds, timelines or credential requests")


def validate_answer(answer, citations, passages, settings) -> list:
    """All output checks, always all of them, so the log shows every result."""
    return [check_private_data(answer),
            check_grounding(answer, citations, passages, settings.grounding_min_overlap),
            check_tone_scope(answer)]
