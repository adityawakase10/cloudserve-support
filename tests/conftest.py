# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Test settings: fast, offline, no API key and no model download needed.

Tests use the lightweight TF-IDF embedder, an in-memory vector index and the
offline extractive generator, so `python -m pytest` runs anywhere, including CI.
"""
import os

import pytest

os.environ.update({
    "EMBEDDING_BACKEND": "tfidf",
    "VECTOR_BACKEND": "memory",
    "LLM_PROVIDER": "offline",
    "RELEVANCE_THRESHOLD": "0.15",
    "CONFIDENCE_THRESHOLD": "0.30",
    "AUTO_RESPOND_ENABLED": "true",
})


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    return tmp_path


@pytest.fixture
def pipeline(tmp_storage):
    from src.pipeline import SupportPipeline
    return SupportPipeline("test-run")


def make_ticket(**overrides):
    base = {"ticket_id": "T-1", "channel": "email", "subject": "Cannot log in",
            "body": "The console says invalid credentials even though my password is correct.",
            "received_at": "2026-03-14T09:22:00Z", "customer_id": "C-1", "customer_name": "Test User",
            "customer_tier": "business", "customer_region": "europe", "language_fluency": "fluent",
            "labels": {}}
    base.update(overrides)
    return base
