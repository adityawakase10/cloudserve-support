# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""A2: all four channels normalise into one shape; bad input never crashes."""
from src.ingest import normalise
from tests.conftest import make_ticket


def test_all_four_channels_normalise():
    for channel in ("email", "chat", "docs_comment", "forum"):
        subject = "" if channel == "chat" else "Webhook retries"
        t = normalise(make_ticket(channel=channel, subject=subject))
        assert t.channel == channel
        assert t.text                                   # something usable downstream
        assert t.original_body                          # original text preserved


def test_email_signature_and_quotes_removed():
    t = normalise(make_ticket(body="My deploy fails.\n> earlier quoted reply\nRegards,\nPriya"))
    assert "quoted" not in t.text and "Priya" not in t.text
    assert "Regards" in t.original_body                 # original kept for audit


def test_empty_and_missing_fields_do_not_crash():
    t = normalise({"channel": "chat"})
    assert t.ticket_id == "MISSING-ID"
    assert "empty ticket" in t.ingest_warnings


def test_unusual_characters_and_unknown_channel():
    t = normalise(make_ticket(channel="fax", body="ｄｅｐｌｏｙ​ failed 🚀\x00"))
    assert t.channel == "unknown"
    assert "\x00" not in t.text


def test_non_dict_record():
    t = normalise(["not", "a", "ticket"])
    assert "record is not a JSON object" in t.ingest_warnings
