# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Print what the system decided for one ticket, readably.

    python -m evaluation.show evaluation/results/run2 VAL-0001
"""
import json
import sys
import textwrap
from pathlib import Path


def main():
    folder, ticket_id = Path(sys.argv[1]), sys.argv[2]
    for line in (folder / "results.jsonl").read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["ticket"]["ticket_id"] != ticket_id:
            continue
        t, o = rec["ticket"], rec["outcome"]
        wrap = lambda s: textwrap.fill(s, 100, initial_indent="  ", subsequent_indent="  ")
        print(f"\n=== {t['ticket_id']}  ({t['channel']}, {t['customer_tier']} customer)")
        print("TICKET:"); print(wrap(t["text"]))
        c = o.get("classification")
        if c:
            print(f"CLASSIFIED: {c['intent']} ({c['intent_confidence']:.0%}), urgency {c['urgency']}, "
                  f"chance docs solve it {c.get('answerable_prob', 0):.0%}")
        for p in o["passages"]:
            print(f"RETRIEVED: {p['passage_id']}  '{p['title']}'  similarity {p['score']:.2f}")
        print(f"\nACTION: {o['action'].upper()}")
        print("REASON:"); print(wrap(o["reason"]))
        if o["answer"]:
            print("\nANSWER SENT:"); print(textwrap.indent(o["answer"], "  "))
        if o["escalation_summary"] and o["action"] != "auto_respond":
            print("\nCONTEXT FOR THE AGENT:"); print(textwrap.indent(o["escalation_summary"], "  "))
        for g in o["guardrails"]:
            print(f"GUARDRAIL {g['name']}: {'pass' if g['passed'] else 'BLOCKED'} - {g['details']}")
        print(f"\nTime {o['latency_s']} s, tokens {o['tokens_used']}\n")
        return
    print(f"{ticket_id} not found in {folder / 'results.jsonl'}")


if __name__ == "__main__":
    main()
