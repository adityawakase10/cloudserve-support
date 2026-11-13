# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Metrics report (A10): computed by code, never by hand.

Groups follow the Build Specification: volume, business, technical, governance,
plus calibration and fairness segments. Label-based figures are only computed
when the input file carries labels.
"""
import statistics
from collections import Counter, defaultdict


def _pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def _p95(values):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, int(round(0.95 * len(ordered))) - 1)]


def compute_metrics(records, decisions_logged: int, decision_rows: int) -> dict:
    """records: list of {"ticket": {...}, "outcome": {...}}."""
    n = len(records)
    actions = Counter(r["outcome"]["action"] for r in records)
    auto = [r for r in records if r["outcome"]["action"] == "auto_respond"]
    latencies = [r["outcome"]["latency_s"] for r in records]
    auto_lat = [r["outcome"]["latency_s"] for r in auto]

    m = {
        "volume": {
            "tickets_processed": n,
            "answered_automatically": actions["auto_respond"],
            "escalated": actions["escalate"],
            "blocked_by_guardrails": actions["block"],
            "by_channel": dict(Counter(r["ticket"]["channel"] for r in records)),
        },
        "business": {
            # Without live customers, an automatic answer that passed every guardrail is
            # counted as resolved on first contact. Repeat contacts cannot be observed offline.
            "first_contact_resolution_pct": _pct(actions["auto_respond"], n),
            "escalation_rate_pct": _pct(actions["escalate"] + actions["block"], n),
            "time_to_first_reply_auto_s": {
                "mean": round(statistics.mean(auto_lat), 2) if auto_lat else None,
                "median": round(statistics.median(auto_lat), 2) if auto_lat else None},
            "time_to_handoff_all_s": {
                "mean": round(statistics.mean(latencies), 2) if latencies else None,
                "median": round(statistics.median(latencies), 2) if latencies else None},
        },
        "technical": {
            "latency_s": {"median": round(statistics.median(latencies), 3) if latencies else None,
                          "p95": _p95(latencies)},
            "tokens_used_total": sum(r["outcome"].get("tokens_used", 0) for r in records),
        },
        "governance": {
            "decisions_logged_final": decisions_logged,
            "decision_rows_all_stages": decision_rows,
            "reconciles_with_tickets": decisions_logged == n,
            "guardrail_activations": dict(Counter(
                g["name"] for r in records for g in r["outcome"]["guardrails"] if not g["passed"])),
            "private_data_detections": sum(
                1 for r in records for g in r["outcome"]["guardrails"]
                if g["name"] == "private_data" and not g["passed"]),
        },
    }

    labelled = [r for r in records if r["ticket"].get("labels", {}).get("intent")]
    if labelled:
        m["technical"].update(_label_metrics(labelled))
        m["governance"]["unsafe_auto_responses"] = sum(
            1 for r in labelled if r["outcome"]["action"] == "auto_respond"
            and r["ticket"]["labels"].get("must_not_auto_respond"))
        m["calibration"] = _calibration(labelled)
        m["fairness"] = _fairness(labelled)
    return m


def _intent(r):
    c = r["outcome"].get("classification")
    return c["intent"] if c else "none"


def _label_metrics(recs) -> dict:
    from sklearn.metrics import precision_recall_fscore_support
    y_true = [r["ticket"]["labels"]["intent"] for r in recs]
    y_pred = [_intent(r) for r in recs]
    classes = sorted(set(y_true))
    p, rcl, _, sup = precision_recall_fscore_support(y_true, y_pred, labels=classes, zero_division=0)
    per_class = {c: {"precision": round(float(p[i]), 3), "recall": round(float(rcl[i]), 3),
                     "support": int(sup[i])} for i, c in enumerate(classes)}

    # Routing: auto_respond vs escalate (block counts as escalate)
    route_true = [r["ticket"]["labels"].get("expected_route") for r in recs]
    route_pred = ["auto_respond" if r["outcome"]["action"] == "auto_respond" else "escalate" for r in recs]
    routing_acc = _pct(sum(a == b for a, b in zip(route_true, route_pred)), len(recs))
    auto_wrong = sum(1 for a, b in zip(route_true, route_pred) if b == "auto_respond" and a == "escalate")
    esc_unneeded = sum(1 for a, b in zip(route_true, route_pred) if b == "escalate" and a == "auto_respond")

    # Retrieval hit rate: for answerable tickets, did we retrieve an expected document?
    answerable = [r for r in recs if r["ticket"]["labels"].get("answerable_from_docs")]
    hits = sum(1 for r in answerable if set(r["ticket"]["labels"].get("expected_doc_ids", []))
               & {p["doc_id"] for p in r["outcome"]["passages"]})
    unanswerable = [r for r in recs if r["ticket"]["labels"].get("answerable_from_docs") is False]
    correct_empty = sum(1 for r in unanswerable if not r["outcome"]["passages"])

    # Citation accuracy (document level): cited docs that are in the expected set
    cited = [(c.split("#")[0], set(r["ticket"]["labels"].get("expected_doc_ids", [])))
             for r in recs if r["outcome"]["action"] == "auto_respond" for c in r["outcome"]["citations"]]
    return {
        "intent_accuracy_pct": _pct(sum(a == b for a, b in zip(y_true, y_pred)), len(recs)),
        "intent_macro_precision": round(float(sum(p) / len(p)), 3),
        "intent_macro_recall": round(float(sum(rcl) / len(rcl)), 3),
        "intent_per_class": per_class,
        "routing_accuracy_pct": routing_acc,
        "auto_answered_but_should_escalate": auto_wrong,
        "escalated_but_could_auto": esc_unneeded,
        "retrieval_hit_rate_pct": _pct(hits, len(answerable)),
        "retrieval_correctly_empty_pct": _pct(correct_empty, len(unanswerable)),
        "citation_accuracy_pct": _pct(sum(1 for d, exp in cited if d in exp), len(cited)),
    }


def _calibration(recs, bands=5) -> list:
    rows = []
    for i in range(bands):
        lo, hi = i / bands, (i + 1) / bands
        grp = [r for r in recs if r["outcome"].get("classification")
               and lo <= r["outcome"]["classification"]["intent_confidence"] < (hi if i < bands - 1 else 1.01)]
        if not grp:
            continue
        stated = statistics.mean(r["outcome"]["classification"]["intent_confidence"] for r in grp)
        observed = sum(1 for r in grp if _intent(r) == r["ticket"]["labels"]["intent"]) / len(grp)
        rows.append({"band": f"{lo:.1f}-{hi:.1f}", "n": len(grp), "stated_pct": round(100 * stated, 1),
                     "observed_pct": round(100 * observed, 1), "gap_pts": round(100 * (stated - observed), 1)})
    return rows


def _fairness(recs) -> dict:
    def length_bucket(r):
        return "long" if len(r["ticket"].get("text", "")) > 160 else "short"
    segments = {
        "customer_tier": lambda r: r["ticket"]["customer_tier"],
        "customer_region": lambda r: r["ticket"]["customer_region"],
        "language_fluency": lambda r: r["ticket"]["language_fluency"],
        "ticket_length": length_bucket,
    }
    out = {}
    for name, key in segments.items():
        groups = defaultdict(list)
        for r in recs:
            groups[key(r)].append(r)
        table = {}
        for g, rs in groups.items():
            route_ok = sum(1 for r in rs if (r["outcome"]["action"] == "auto_respond") ==
                           (r["ticket"]["labels"].get("expected_route") == "auto_respond"))
            table[g] = {"n": len(rs),
                        "auto_resolution_pct": _pct(sum(r["outcome"]["action"] == "auto_respond" for r in rs), len(rs)),
                        "intent_accuracy_pct": _pct(sum(_intent(r) == r["ticket"]["labels"]["intent"] for r in rs), len(rs)),
                        "routing_accuracy_pct": _pct(route_ok, len(rs))}
        accs = [v["routing_accuracy_pct"] for v in table.values() if v["n"] >= 5]
        out[name] = {"groups": table,
                     "max_gap_routing_accuracy_pts": round(max(accs) - min(accs), 1) if len(accs) > 1 else None}
    return out


def render_markdown(m: dict, meta: dict) -> str:
    v, b, t, g = m["volume"], m["business"], m["technical"], m["governance"]
    L = [f"# Metrics report", "",
         f"- Run ID: {meta['run_id']}", f"- Input: {meta['input']}", f"- Started: {meta['started']}",
         f"- Duration: {meta['duration_s']} s", f"- Model: {meta['model']}",
         f"- Settings: {meta['settings']}", "",
         "## Volume", f"| Tickets processed | Answered automatically | Escalated | Blocked by guardrails |",
         "|---|---|---|---|",
         f"| {v['tickets_processed']} | {v['answered_automatically']} | {v['escalated']} | {v['blocked_by_guardrails']} |", "",
         "## Business outcomes (baseline from CloudServe history)",
         "| Measure | Baseline | Target | This run |", "|---|---|---|---|",
         f"| First contact resolution | 42% | ≥ 60% | {b['first_contact_resolution_pct']}% |",
         f"| Escalation rate (incl. blocked) | 58% | ≤ 30% | {b['escalation_rate_pct']}% |",
         f"| Time to first reply, auto-answered (mean / median) | 8–12 hours | < 5 min | "
         f"{b['time_to_first_reply_auto_s']['mean']} s / {b['time_to_first_reply_auto_s']['median']} s |",
         f"| Time to hand-off, all tickets (mean / median) | — | — | "
         f"{b['time_to_handoff_all_s']['mean']} s / {b['time_to_handoff_all_s']['median']} s |", "",
         "## Technical", "| Measure | Value |", "|---|---|",
         f"| Latency median / p95 (s) | {t['latency_s']['median']} / {t['latency_s']['p95']} |",
         f"| Tokens used (cache hits cost 0) | {t['tokens_used_total']} |"]
    for k in ["intent_accuracy_pct", "intent_macro_precision", "intent_macro_recall", "routing_accuracy_pct",
              "auto_answered_but_should_escalate", "escalated_but_could_auto", "retrieval_hit_rate_pct",
              "retrieval_correctly_empty_pct", "citation_accuracy_pct"]:
        if k in t:
            L.append(f"| {k} | {t[k]} |")
    L += ["", "## Governance", "| Measure | Value |", "|---|---|",
          f"| Final decisions logged / tickets processed | {g['decisions_logged_final']} / {v['tickets_processed']} "
          f"({'reconciles' if g['reconciles_with_tickets'] else 'DOES NOT RECONCILE'}) |",
          f"| Decision rows, all stages | {g['decision_rows_all_stages']} |",
          f"| Guardrail activations by type | {g['guardrail_activations'] or 'none'} |",
          f"| Private data detections | {g['private_data_detections']} |"]
    if "unsafe_auto_responses" in g:
        L.append(f"| Auto-answers on never-automate tickets | {g['unsafe_auto_responses']} |")
    if "intent_per_class" in t:
        L += ["", "## Intent precision and recall per class", "| Intent | Precision | Recall | Support |",
              "|---|---|---|---|"]
        L += [f"| {c} | {s['precision']} | {s['recall']} | {s['support']} |" for c, s in t["intent_per_class"].items()]
    if m.get("calibration"):
        L += ["", "## Confidence calibration (intent)", "| Band | n | Stated % | Observed % | Gap (pts) |",
              "|---|---|---|---|---|"]
        L += [f"| {r['band']} | {r['n']} | {r['stated_pct']} | {r['observed_pct']} | {r['gap_pts']} |"
              for r in m["calibration"]]
    if m.get("fairness"):
        L += ["", "## Fairness segments"]
        for seg, data in m["fairness"].items():
            L += [f"### {seg} (max routing-accuracy gap: {data['max_gap_routing_accuracy_pts']} pts)",
                  "| Group | n | Auto-resolved % | Intent accuracy % | Routing accuracy % |", "|---|---|---|---|---|"]
            L += [f"| {grp} | {s['n']} | {s['auto_resolution_pct']} | {s['intent_accuracy_pct']} | "
                  f"{s['routing_accuracy_pct']} |" for grp, s in sorted(data["groups"].items())]
    L += ["", "_Figures are produced by evaluation/metrics.py from this run's results. "
              "First contact resolution assumes an automatic answer that passed every guardrail resolves the ticket; "
              "repeat contacts and real satisfaction cannot be observed offline._"]
    return "\n".join(L)
