# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Evaluation harness: process a whole ticket file unattended (A9) and write
a metrics report (A10).

Usage (from the project root):
    python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/

Writes into the output folder:
    results.jsonl       one line per ticket: what the system did and why
    decisions.csv       this run's decision log (also stored in storage/decisions.db)
    metrics.json        every figure, machine-readable
    metrics_report.md   the same figures as a readable report
"""
import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from evaluation.metrics import compute_metrics, render_markdown
from src.config import get_settings
from src.ingest import load_tickets
from src.monitoring import observe, start_metrics_server
from src.pipeline import SupportPipeline


def _unique_ids(raw_tickets):
    """Duplicate or missing IDs would break log reconciliation, so make every ID unique."""
    seen = set()
    for i, t in enumerate(raw_tickets):
        if not isinstance(t, dict):
            continue
        tid = str(t.get("ticket_id") or f"MISSING-ID-{i:04d}")
        if tid in seen:
            tid = f"{tid}-dup{i}"
        seen.add(tid)
        t["ticket_id"] = tid
    return raw_tickets


def run(input_path: str, output_dir: str, limit: int = None, metrics_port: int = None) -> dict:
    settings = get_settings()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.time()

    raw = _unique_ids(load_tickets(input_path))
    if limit:
        raw = raw[:limit]
    if metrics_port:
        start_metrics_server(metrics_port)

    print(f"[{run_id}] loading models and documentation...", flush=True)
    pipeline = SupportPipeline(run_id, settings)
    print(f"[{run_id}] processing {len(raw)} tickets from {input_path}", flush=True)

    records = []
    with open(out / "results.jsonl", "w", encoding="utf-8") as f:
        for i, item in enumerate(raw, 1):
            ticket, outcome = pipeline.process(item)
            observe(outcome, ticket.channel)
            rec = {"ticket": asdict(ticket), "outcome": outcome.to_dict()}
            records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()                                     # partial results survive a crash
            print(f"  {i:>4}/{len(raw)}  {ticket.ticket_id:<14} {outcome.action:<13} "
                  f"{outcome.latency_s:>6.2f}s  {outcome.reason[:70]}", flush=True)

    metrics = compute_metrics(records, pipeline.log.count_final(), pipeline.log.count_rows())
    meta = {"run_id": run_id, "input": str(input_path), "started": started,
            "duration_s": round(time.time() - t0, 1),
            "model": pipeline.model_label,
            "settings": {k: getattr(settings, k) for k in (
                "embedding_backend", "vector_backend", "chunk_strategy", "retrieval_top_k",
                "relevance_threshold", "confidence_threshold", "grounding_min_overlap", "prompt_version")}}
    (out / "metrics.json").write_text(json.dumps({"meta": meta, "metrics": metrics}, indent=2, default=str),
                                      encoding="utf-8")
    (out / "metrics_report.md").write_text(render_markdown(metrics, meta), encoding="utf-8")
    pipeline.log.export_csv(out / "decisions.csv")
    print(f"[{run_id}] done in {meta['duration_s']} s. Report: {out / 'metrics_report.md'}", flush=True)
    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the support pipeline over a ticket file, unattended.")
    parser.add_argument("--input", required=True, help="Path to a JSON file containing a list of tickets")
    parser.add_argument("--output", required=True, help="Folder to write results and the metrics report into")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N tickets (for quick checks)")
    parser.add_argument("--metrics-port", type=int, default=None, help="Expose Prometheus metrics on this port")
    args = parser.parse_args(argv)
    try:
        run(args.input, args.output, args.limit, args.metrics_port)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not read input file: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
