# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Discovery analysis: check stakeholder claims against the development tickets.

Run from the project root:
    python analysis/discovery_analysis.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/development_tickets.json")
tickets = json.loads(path.read_text(encoding="utf-8"))

# Flatten nested blocks: labels.intent -> column "labels.intent", etc.
df = pd.json_normalize(tickets)


def pct(series):
    """Share of each value, as percentages rounded to 1 decimal."""
    return (series.value_counts(normalize=True) * 100).round(1)


print(f"Tickets: {len(df)}\n")

print("== Channel mix (%) ==")
print(pct(df["channel"]), "\n")

print("== Top 10 intents (%) ==")
print(pct(df["labels.intent"]).head(10), "\n")

print("== Urgency mix (%) ==")
print(pct(df["labels.urgency"]), "\n")

print("== Historical baseline ==")
print("First contact resolution: ", round(df["history.first_contact_resolution"].mean() * 100, 1), "%")
print("Escalation rate:          ", round(df["history.escalated"].mean() * 100, 1), "%")
print("Average CSAT:             ", round(df["history.csat_rating"].mean(), 2), "/ 5")
print("Repeat contacts:          ", round(df["history.repeat_contact"].mean() * 100, 1), "%\n")

print("== Answerable from existing documentation ==")
print("All tickets:", round(df["labels.answerable_from_docs"].mean() * 100, 1), "%")

# TODO (you): keep only the tickets that were escalated historically.
# Hint: same pattern as filtering any DataFrame by a True/False column -> df[ condition ]
escalated = df[df["history.escalated"]]

print("Escalated tickets that WERE answerable from docs:",
      round(escalated["labels.answerable_from_docs"].mean() * 100, 1), "%\n")

print("== 'Never automate' tickets (labels.must_not_auto_respond) ==")
print(round(df["labels.must_not_auto_respond"].mean() * 100, 1), "% of all tickets\n")

print("== Intents with the LOWEST share answerable from docs ==")
print((df.groupby("labels.intent")["labels.answerable_from_docs"].mean() * 100)
        .round(0).sort_values().head(6), "\n")

print("== Outcomes by language fluency ==")
print(df.groupby("language_fluency")[["history.csat_rating", "history.first_contact_resolution"]]
        .mean().round(2), "\n")

print("== Outcomes by customer tier ==")
print(df.groupby("customer_tier")[["history.resolution_time_minutes", "history.csat_rating"]]
        .median().round(1), "\n")

print("== Median resolution time (minutes) by urgency ==")
print(df.groupby("labels.urgency")["history.resolution_time_minutes"].median())