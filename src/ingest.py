# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Ingest: turn tickets from all four channels into one Ticket shape.

Acceptance criterion A2. Must never crash on missing fields, odd characters
or empty bodies (A11), so every field has a safe default.
"""
import json
import re
import unicodedata
from pathlib import Path

from src.models import Ticket

KNOWN_CHANNELS = {"email", "chat", "docs_comment", "forum"}

# Email signatures and quoted replies add noise without adding meaning.
_SIGNATURE = re.compile(r"\n\s*(--|regards|thanks,|best,|sent from my)\b.*$", re.IGNORECASE | re.DOTALL)
_QUOTED_LINE = re.compile(r"^\s*>.*$", re.MULTILINE)


def _clean(text) -> str:
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)                 # unify odd unicode forms
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t")
    return text.strip()


def _channel_text(channel: str, subject: str, body: str) -> str:
    """Channel-specific cleanup lives here and nowhere else downstream."""
    if channel == "email":
        body = _QUOTED_LINE.sub("", body)
        body = _SIGNATURE.sub("", body)
    if channel == "forum":
        body = _QUOTED_LINE.sub("", body)                       # quoted posts from other users
    # Chat has no subject; docs comments and forum posts often have short ones.
    combined = f"{subject}. {body}" if subject else body
    return re.sub(r"\s+", " ", combined).strip()


def normalise(raw) -> Ticket:
    """Convert one raw ticket (any channel) into a Ticket. Never raises."""
    warnings = []
    if not isinstance(raw, dict):
        warnings.append("record is not a JSON object")
        raw = {}

    channel = _clean(raw.get("channel")).lower()
    if channel not in KNOWN_CHANNELS:
        warnings.append(f"unknown channel '{channel}'")
        channel = "unknown"

    subject = _clean(raw.get("subject"))
    body = _clean(raw.get("body"))
    if not body and not subject:
        warnings.append("empty ticket")

    ticket_id = _clean(raw.get("ticket_id")) or "MISSING-ID"
    if ticket_id == "MISSING-ID":
        warnings.append("missing ticket_id")

    return Ticket(
        ticket_id=ticket_id,
        channel=channel,
        text=_channel_text(channel, subject, body),
        original_subject=subject,
        original_body=body,
        received_at=_clean(raw.get("received_at")),
        customer_id=_clean(raw.get("customer_id")),
        customer_name=_clean(raw.get("customer_name")),
        customer_tier=_clean(raw.get("customer_tier")) or "unknown",
        customer_region=_clean(raw.get("customer_region")) or "unknown",
        language_fluency=_clean(raw.get("language_fluency")) or "unknown",
        labels=raw.get("labels") if isinstance(raw.get("labels"), dict) else {},
        ingest_warnings=warnings,
    )


def load_tickets(path) -> list:
    """Load a ticket file. Returns raw records; a broken file raises a clear error."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tickets" in data:
        data = data["tickets"]
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list of tickets")
    return data
