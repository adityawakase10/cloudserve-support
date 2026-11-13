# Metrics report

- Run ID: run-20261113T170127Z
- Input: data/validation_tickets.json
- Started: 2026-11-13T17:01:27.760776+00:00
- Duration: 460.1 s
- Model: openai/gpt-oss-20b
- Settings: {'embedding_backend': 'sentence-transformers', 'vector_backend': 'chroma', 'chunk_strategy': 'whole', 'retrieval_top_k': 3, 'relevance_threshold': 0.4, 'confidence_threshold': 0.5, 'grounding_min_overlap': 0.5, 'prompt_version': 'PR-01 v1.1'}

## Volume
| Tickets processed | Answered automatically | Escalated | Blocked by guardrails |
|---|---|---|---|
| 80 | 50 | 30 | 0 |

## Business outcomes (baseline from CloudServe history)
| Measure | Baseline | Target | This run |
|---|---|---|---|
| First contact resolution | 42% | ≥ 60% | 62.5% |
| Escalation rate (incl. blocked) | 58% | ≤ 30% | 37.5% |
| Time to first reply, auto-answered (mean / median) | 8–12 hours | < 5 min | 8.82 s / 1.4 s |
| Time to hand-off, all tickets (mean / median) | — | — | 5.53 s / 0.91 s |

## Technical
| Measure | Value |
|---|---|
| Latency median / p95 (s) | 0.915 / 53.631 |
| Tokens used (cache hits cost 0) | 45111 |
| intent_accuracy_pct | 100.0 |
| intent_macro_precision | 1.0 |
| intent_macro_recall | 1.0 |
| routing_accuracy_pct | 70.0 |
| auto_answered_but_should_escalate | 13 |
| escalated_but_could_auto | 11 |
| retrieval_hit_rate_pct | 92.5 |
| retrieval_correctly_empty_pct | 37.0 |
| citation_accuracy_pct | 67.9 |

## Governance
| Measure | Value |
|---|---|
| Final decisions logged / tickets processed | 80 / 80 (reconciles) |
| Decision rows, all stages | 420 |
| Guardrail activations by type | none |
| Private data detections | 0 |
| Auto-answers on never-automate tickets | 0 |

## Intent precision and recall per class
| Intent | Precision | Recall | Support |
|---|---|---|---|
| account_access | 1.0 | 1.0 | 4 |
| api_key_issue | 1.0 | 1.0 | 6 |
| api_usage_question | 1.0 | 1.0 | 4 |
| authentication_failure | 1.0 | 1.0 | 3 |
| billing_query | 1.0 | 1.0 | 10 |
| compliance_request | 1.0 | 1.0 | 1 |
| configuration_help | 1.0 | 1.0 | 3 |
| data_export | 1.0 | 1.0 | 1 |
| data_residency | 1.0 | 1.0 | 6 |
| database_issue | 1.0 | 1.0 | 1 |
| deployment_failure | 1.0 | 1.0 | 5 |
| feature_request | 1.0 | 1.0 | 3 |
| integration_help | 1.0 | 1.0 | 3 |
| onboarding | 1.0 | 1.0 | 4 |
| performance_degradation | 1.0 | 1.0 | 3 |
| quota_or_overage | 1.0 | 1.0 | 2 |
| rate_limit | 1.0 | 1.0 | 1 |
| rollback_request | 1.0 | 1.0 | 6 |
| security_incident | 1.0 | 1.0 | 4 |
| sso_configuration | 1.0 | 1.0 | 1 |
| unclear_request | 1.0 | 1.0 | 6 |
| webhook_issue | 1.0 | 1.0 | 3 |

## Confidence calibration (intent)
| Band | n | Stated % | Observed % | Gap (pts) |
|---|---|---|---|---|
| 0.6-0.8 | 4 | 66.1 | 100.0 | -33.9 |
| 0.8-1.0 | 76 | 92.6 | 100.0 | -7.4 |

## Fairness segments
### customer_tier (max routing-accuracy gap: 35.7 pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| business | 30 | 80.0 | 100.0 | 70.0 |
| enterprise | 8 | 75.0 | 100.0 | 100.0 |
| standard | 42 | 47.6 | 100.0 | 64.3 |
### customer_region (max routing-accuracy gap: 21.7 pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| asia_pacific | 21 | 66.7 | 100.0 | 76.2 |
| europe | 25 | 68.0 | 100.0 | 64.0 |
| latin_america | 7 | 28.6 | 100.0 | 85.7 |
| north_america | 27 | 63.0 | 100.0 | 66.7 |
### language_fluency (max routing-accuracy gap: 2.1 pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| fluent | 61 | 62.3 | 100.0 | 70.5 |
| non_fluent | 19 | 63.2 | 100.0 | 68.4 |
### ticket_length (max routing-accuracy gap: 14.5 pts)
| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |
|---|---|---|---|---|
| long | 37 | 67.6 | 100.0 | 62.2 |
| short | 43 | 58.1 | 100.0 | 76.7 |

_Figures are produced by evaluation/metrics.py from this run's results. First contact resolution assumes an automatic answer that passed every guardrail resolves the ticket; repeat contacts and real satisfaction cannot be observed offline._