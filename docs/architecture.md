# Architecture

Drafted with Claude (Anthropic), reviewed by Aditya Wakase.

![Architecture](architecture.png)

```mermaid
flowchart TB
  A["Ticket<br/>email · chat · docs comment · forum"] --> B["Ingest<br/>normalise 4 channels"]
  B --> C{"Input guardrail<br/>instruction-like text?"}
  C -- yes --> X["BLOCK<br/>held for review"]
  C -- no --> D["Classify<br/>intent · urgency · answerability<br/>(embeddings + logistic regression,<br/>no API tokens)"]
  D --> E["Retrieve<br/>29 articles · Chroma · MiniLM<br/>top-3 above 0.40"]
  E --> F{"Route<br/>never-automate? confidence &lt; 0.50?<br/>answerability &lt; 0.60? no passage?"}
  F -- escalate --> G["ESCALATE<br/>with context: topic, sources,<br/>what it was unsure about"]
  F -- proceed --> H["Generate<br/>Groq gpt-oss-20b · prompt PR-01 v1.1<br/>cited JSON answer"]
  H --> I{"Output guardrails<br/>private data · grounding · tone/scope"}
  I -- fail --> X
  I -- pass --> J["AUTO-RESPOND<br/>with citation + 'automated' notice"]
  B -.-> L[("Decision log<br/>SQLite, every stage")]
  D -.-> L
  E -.-> L
  F -.-> L
  H -.-> L
  I -.-> L
  K["Kill switch<br/>storage/KILL_SWITCH"] -.-> F
```

## Components

| Module | Role | Requirement |
|---|---|---|
| `src/ingest.py` | Normalise 4 channels into one Ticket shape; never raises | FR-01 |
| `src/guardrails.py` (input) | Block instruction-like tickets before the model | FR-06 |
| `src/classify.py` | Intent, urgency, answerability (MiniLM + logistic regression, no API calls) | FR-02, FR-13 |
| `src/retrieve.py` | Chunk 29 articles, Chroma index, top-3 above relevance threshold | FR-03 |
| `src/route.py` | Ordered, deterministic rules with plain-language reasons; escalation package | FR-04, FR-07 |
| `src/generate.py`, `src/llm.py` | Cited JSON answer via Groq; cache, pacing, retries, circuit breaker | FR-05, FR-09 |
| `src/guardrails.py` (output) | Private data, grounding, tone/scope | FR-06 |
| `src/logging_store.py` | SQLite decision log, one row per stage | FR-08 |
| `evaluation/harness.py`, `metrics.py` | Unattended run + metrics report | A9, A10 |

## Decisions (set in `.env`, measured with `python -m evaluation.tune`)

| Setting | Value | Why |
|---|---|---|
| CHUNK_STRATEGY | whole | Higher hit rate with less retrieval on unanswerable tickets; keeps resolution steps intact |
| RELEVANCE_THRESHOLD | 0.40 | 91.6% hit rate on answerable development tickets |
| CONFIDENCE_THRESHOLD | 0.50 | 99.3% topic accuracy on tickets that pass |
| ANSWERABLE_THRESHOLD | 0.60 | Compromise between wrong answers and automatic resolution (PRD v2.0, FR-13) |
| Never-automate intents | security, compliance, data residency, feature request, unclear | Daniel's interview; labels; gate-run evidence |
