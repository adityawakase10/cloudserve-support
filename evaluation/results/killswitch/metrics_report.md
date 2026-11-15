# Metrics report

- Run ID: run-20261115T081010Z
- Input: data/validation_tickets.json
- Started: 2026-11-15T08:10:10.872935+00:00
- Duration: 68.3 s
- Model: openai/gpt-oss-20b
- Settings: {'embedding_backend': 'sentence-transformers', 'vector_backend': 'chroma', 'chunk_strategy': 'whole', 'retrieval_top_k': 3, 'relevance_threshold': 0.4, 'confidence_threshold': 0.5, 'grounding_min_overlap': 0.5, 'prompt_version': 'PR-01 v1.1'}

## Volume
| Tickets processed | Answered automatically | Escalated | Blocked by guardrails |
|---|---|---|---|
| 3 | 0 | 3 | 0 |

## Business outcomes (baseline from CloudServe history)
| Measure | Baseline | Target | This run |
|---|---|---|---|
| First contact resolution | 42% | ≥ 60% | 0.0% |
| Escalation rate (incl. blocked) | 58% | ≤ 30% | 100.0% |
| Time to first reply, auto-answered (mean / median) | 8–12 hours | < 5 min | None s / None s |
| Time to hand-off, all tickets (mean / median) | — | — | 0.33 s / 0.23 s |

## Technical
| Measure | Value |
|---|---|
| Latency median / p95 (s) | 0.227 / 0.557 |
| Tokens used (cache hits cost 0) | 0 |
| intent_accuracy_pct | 100.0 |
| intent_macro_precision | 1.0 |
| intent_macro_recall | 1.0 |
| routing_accuracy_pct | 66.7 |
| auto_answered_but_should_escalate | 0 |
| escalated_but_could_auto | 1 |
| retrieval_hit_rate_pct | 100.0 |
| retrieval_correctly_empty_pct | 100.0 |
| citation_accuracy_pct | None |

## Governance
| Measure | Value |
|---|---|
| Final decisions logged / tickets processed | 3 / 3 (reconciles) |
| Decision rows, all stages | 12 |
| Guardrail activations by type | none |
| Private data detections | 0 |
| Auto-answers on never-automate tickets | 0 |

## Intent precision and recall per class
| Intent | Precision | Recall | Support |
|---|---|---|---|
| api_key_issue | 1.0 | 1.0 | 1 |
| unclear_request | 1.0 | 1.0 | 2 |

## Confidence calibration (intent)
| Band | n | Stated % | Observed % | Gap (pts) |
|---|---|---|---|---|
| 0.8-1.0 | 3 | 87.0 | 100.0 | -13.0 |

## Fairness segments
### customer_tier (max routing-accuracy gap: None pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| business | 1 | 0.0 | 100.0 | 0.0 |
| standard | 2 | 0.0 | 100.0 | 100.0 |
### customer_region (max routing-accuracy gap: None pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| asia_pacific | 1 | 0.0 | 100.0 | 0.0 |
| europe | 1 | 0.0 | 100.0 | 100.0 |
| north_america | 1 | 0.0 | 100.0 | 100.0 |
### language_fluency (max routing-accuracy gap: None pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| fluent | 2 | 0.0 | 100.0 | 50.0 |
| non_fluent | 1 | 0.0 | 100.0 | 100.0 |
### ticket_length (max routing-accuracy gap: None pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| long | 1 | 0.0 | 100.0 | 0.0 |
| short | 2 | 0.0 | 100.0 | 100.0 |

_Figures are produced by evaluation/metrics.py from this run's results. First contact resolution assumes an automatic answer that passed every guardrail resolves the ticket; repeat contacts and real satisfaction cannot be observed offline._