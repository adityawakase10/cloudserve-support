# CloudServe support assistant (FDE capstone)

CloudServe asked for a chatbot. Discovery showed that most answers already exist in their
documentation, but agents and customers cannot find them, and escalations reach senior engineers
with no context. This system answers what the documentation can support, with citations, and
escalates everything else to a human **with the context already attached**: likely topic, relevant
documents, and what it was unsure about.

```
ticket ─► ingest ─► input guardrail ─► classify ─► retrieve ─► route ─┬─► generate ─► output guardrails ─► auto-respond
                                                                      └─► escalate / block (with context)      every step ─► decision log
```

## Requirements

- Python 3.13 (tested on 3.13.9)
- About 2 GB free disk for packages and the embedding model
- A free Groq API key: https://console.groq.com → API Keys
- Internet access on first run (downloads the `all-MiniLM-L6-v2` embedding model, about 90 MB)

## Setup

**Windows (PowerShell)**
```powershell
git clone <this-repo-url> cloudserve-support
cd cloudserve-support
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux**
```bash
git clone <this-repo-url> cloudserve-support
cd cloudserve-support
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` and replace `your_key_here` with your Groq key.

## Run

All commands are run from the project root with the virtual environment active.

**Full unattended evaluation run** (the main command):
```
python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/
```
Point `--input` at any ticket file with the same schema. Outputs in the `--output` folder:
`results.jsonl` (every ticket: action, reason, answer, sources), `metrics_report.md`,
`metrics.json`, `decisions.csv`. The full decision log is also in `storage/decisions.db`.
Add `--limit 5` for a quick check.

**Failure-handling demo:** a prompt injection, an empty ticket, a security incident, garbled
characters on an unknown channel, a duplicate ID and a record that is not a ticket:
```
python -m evaluation.harness --input data/demo_failure_tickets.json --output evaluation/results/demo
```
To see the provider-outage path, set `GROQ_API_KEY=invalid` and `LLM_CACHE_ENABLED=false` in `.env`
(or disconnect from the internet) and run the main command with `--limit 8`: tickets that would have been
answered are escalated with context instead, and nothing crashes. Restore both settings afterwards.

**Tests** (offline, no key needed):
```
python -m pytest tests/ -v
```

**API** (optional):
```
uvicorn src.api:app --port 8000
```
then open http://localhost:8000/docs.

**Threshold tuning** (development tickets only):
```
python -m evaluation.tune
```

## Kill switch

Stop all automatic answers immediately, without a restart: create the file `storage/KILL_SWITCH`
(any content). Every ticket is then escalated. Delete the file to resume. Alternatively, set
`AUTO_RESPOND_ENABLED=false` in `.env`.

## Project layout

| Path | What it is |
|---|---|
| `src/ingest.py` | Normalises email, chat, docs comments and forum posts into one shape |
| `src/classify.py` | Intent and urgency with confidence (embeddings + logistic regression, no API calls) |
| `src/retrieve.py` | Chunking and vector search over the 29 articles (Chroma) with a relevance threshold |
| `src/route.py` | Deterministic answer-or-escalate rules with plain-language reasons |
| `src/generate.py`, `src/llm.py` | Cited answers via Groq: caching, rate pacing, retries, circuit breaker |
| `src/guardrails.py` | Prompt injection, private data, grounding, and commitment checks that block |
| `src/logging_store.py` | SQLite decision log (one row per stage per ticket) |
| `evaluation/harness.py`, `evaluation/metrics.py` | Unattended run and metrics report |
| `prompts/` | Versioned prompt library |
| `docs/` | Architecture and decision notes |

## AI assistance

Most of the code was drafted with Claude (Anthropic) and reviewed, run and modified by me. Each such
file says so in its first line. The design decisions (thresholds, chunking, routing rules, guardrail
scope) were made by me from the measurements in `evaluation/tune.py` and the discovery evidence.
