# Metrics report

- Run ID: run-20261114T135252Z
- Input: data/demo_failure_tickets.json
- Started: 2026-11-14T13:52:52.355318+00:00
- Duration: 48.0 s
- Model: openai/gpt-oss-20b
- Settings: {'embedding_backend': 'sentence-transformers', 'vector_backend': 'chroma', 'chunk_strategy': 'whole', 'retrieval_top_k': 3, 'relevance_threshold': 0.4, 'confidence_threshold': 0.5, 'grounding_min_overlap': 0.5, 'prompt_version': 'PR-01 v1.1'}

## Volume
| Tickets processed | Answered automatically | Escalated | Blocked by guardrails |
|---|---|---|---|
| 6 | 0 | 5 | 1 |

## Business outcomes (baseline from CloudServe history)
| Measure | Baseline | Target | This run |
|---|---|---|---|
| First contact resolution | 42% | ≥ 60% | 0.0% |
| Escalation rate (incl. blocked) | 58% | ≤ 30% | 100.0% |
| Time to first reply, auto-answered (mean / median) | 8–12 hours | < 5 min | None s / None s |
| Time to hand-off, all tickets (mean / median) | — | — | 0.17 s / 0.12 s |

## Technical
| Measure | Value |
|---|---|
| Latency median / p95 (s) | 0.119 / 0.434 |
| Tokens used (cache hits cost 0) | 0 |

## Governance
| Measure | Value |
|---|---|
| Final decisions logged / tickets processed | 6 / 6 (reconciles) |
| Decision rows, all stages | 22 |
| Guardrail activations by type | {'instruction_integrity': 1} |
| Private data detections | 0 |

_Figures are produced by evaluation/metrics.py from this run's results. First contact resolution assumes an automatic answer that passed every guardrail resolves the ticket; repeat contacts and real satisfaction cannot be observed offline._