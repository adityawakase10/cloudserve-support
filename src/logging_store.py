# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Decision log: every automated decision written to SQLite (A8).

Schema follows the Governance Framework's minimum record. One row per stage
(classification, retrieval, routing, generation, validation, final) so any
decision can be reconstructed months later. Every processed ticket gets
exactly one "final" row: that is what reconciles against tickets processed.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    decision_id      TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    ticket_id        TEXT NOT NULL,
    stage            TEXT NOT NULL,
    input_summary    TEXT,
    model            TEXT,
    prediction       TEXT,
    confidence       REAL,
    alternatives     TEXT,
    sources_used     TEXT,
    threshold        REAL,
    action_taken     TEXT NOT NULL,
    reason           TEXT NOT NULL,
    guardrails       TEXT,
    prompt_version   TEXT,
    requirement_ids  TEXT
)"""


class DecisionLog:
    def __init__(self, db_path, run_id: str):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(SCHEMA)
        self.conn.commit()
        self.run_id = run_id

    def record(self, ticket_id, stage, action_taken, reason, *, input_summary="", model="",
               prediction="", confidence=None, alternatives=None, sources=None, threshold=None,
               guardrails=None, prompt_version="", requirement_ids=None):
        self.conn.execute(
            "INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), self.run_id, datetime.now(timezone.utc).isoformat(), ticket_id, stage,
             input_summary[:300], model, prediction, confidence,
             json.dumps(alternatives or []), json.dumps(sources or []), threshold,
             action_taken, reason, json.dumps(guardrails or {}), prompt_version,
             json.dumps(requirement_ids or [])))
        self.conn.commit()

    def count_final(self, run_id=None) -> int:
        cur = self.conn.execute("SELECT COUNT(DISTINCT ticket_id) FROM decisions "
                                "WHERE run_id=? AND stage='final'", (run_id or self.run_id,))
        return cur.fetchone()[0]

    def count_rows(self, run_id=None) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM decisions WHERE run_id=?", (run_id or self.run_id,))
        return cur.fetchone()[0]

    def export_csv(self, path, run_id=None):
        import csv
        cur = self.conn.execute("SELECT * FROM decisions WHERE run_id=? ORDER BY created_at",
                                (run_id or self.run_id,))
        cols = [d[0] for d in cur.description]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(cur.fetchall())
