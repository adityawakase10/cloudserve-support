# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""All settings in one place, read from environment variables (.env).

Why: thresholds and model names are decisions that change; keeping them out of
the code means changing a decision never means editing logic.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Keep the downloaded embedding model inside the project (not in the user profile on C:).
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / "storage" / "hf_cache"))


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    # --- Model provider -------------------------------------------------
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq"))  # groq | offline
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "openai/gpt-oss-20b"))
    llm_base_url: str = field(default_factory=lambda: os.getenv(
        "LLM_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"))
    llm_timeout_s: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_S", "30")))
    llm_max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "4")))
    # Free tier: ~8,000 tokens per minute. We stay under 90% of it.
    llm_tokens_per_minute: int = field(default_factory=lambda: int(os.getenv("LLM_TOKENS_PER_MINUTE", "8000")))

    # --- Embeddings and vector store (swappable) --------------------------
    embedding_backend: str = field(default_factory=lambda: os.getenv("EMBEDDING_BACKEND", "sentence-transformers"))  # or tfidf
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    vector_backend: str = field(default_factory=lambda: os.getenv("VECTOR_BACKEND", "chroma"))  # or memory

    # --- Paths --------------------------------------------------------------
    docs_path: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("DOCS_PATH", "data/documentation.json"))
    train_path: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("TRAIN_PATH", "data/development_tickets.json"))
    storage_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("STORAGE_DIR", "storage"))

    # --- DECISIONS (set from data, see evaluation/tune.py) -----------------
    # Chunking: "whole" = one passage per article, "section" = split on ## headings.
    chunk_strategy: str = field(default_factory=lambda: os.getenv("CHUNK_STRATEGY", "section"))
    retrieval_top_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "3")))
    # Passages scoring below this similarity are treated as "no relevant doc".
    relevance_threshold: float = field(default_factory=lambda: float(os.getenv("RELEVANCE_THRESHOLD", "0.35")))
    # Intent confidence below this always escalates.
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.50")))
    # Probability (from the answerability classifier) that the docs can solve THIS
    # specific ticket. Below this, escalate even if a related article was found.
    answerable_threshold: float = field(default_factory=lambda: float(os.getenv("ANSWERABLE_THRESHOLD", "0.50")))
    # Share of an answer's words that must appear in the cited passages.
    grounding_min_overlap: float = field(default_factory=lambda: float(os.getenv("GROUNDING_MIN_OVERLAP", "0.5")))

    # --- Governance ---------------------------------------------------------
    # Kill switch: when false, nothing is sent automatically; everything escalates.
    auto_respond_enabled: bool = field(default_factory=lambda: _bool("AUTO_RESPOND_ENABLED", True))
    prompt_version: str = "PR-01 v1.1"

    @property
    def db_path(self) -> Path:
        return self.storage_dir / "decisions.db"

    @property
    def kill_switch_file(self) -> Path:
        # Creating this file stops automatic answers immediately, no restart needed.
        return self.storage_dir / "KILL_SWITCH"


# Intents that must never be answered automatically. Source: labels.must_not_auto_respond
# in the development data (security, compliance, feature requests, unclear requests),
# PLUS data_residency because Daniel (tier 2) said data-location questions carry
# compliance risk and must always reach a human, even though the labels allow it.
NEVER_AUTO_INTENTS = {"security_incident", "compliance_request", "feature_request", "unclear_request",
                      "data_residency"}


def get_settings() -> Settings:
    """Read settings fresh each time, so tests and the kill switch take effect immediately."""
    return Settings()
