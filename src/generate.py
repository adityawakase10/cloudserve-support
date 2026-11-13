# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Generate: draft a cited answer from the retrieved passages (A6).

- Instructions (system message) and customer text (user message, inside
  <ticket> tags) are kept separate, so ticket text cannot redirect the model.
- The model must return JSON our code can parse; anything else is treated as
  "cannot answer" rather than sent.
- "offline" provider: an extractive stand-in used by tests and CI, so they
  never need an API key.
"""
import json
import re

from src.config import PROJECT_ROOT
from src.llm import LLMClient, ProviderError

PROMPT_FILE = PROJECT_ROOT / "prompts" / "build" / "answer_v1.md"


def _safe(text: str) -> str:
    # Stop a ticket from closing our delimiter tags early.
    return text.replace("<", "(").replace(">", ")")


def build_messages(ticket, passages) -> list:
    system = PROMPT_FILE.read_text(encoding="utf-8")
    docs = "\n\n".join(f'<passage id="{p.passage_id}">\n{p.text}\n</passage>' for p in passages)
    user = (f"<passages>\n{docs}\n</passages>\n\n"
            f"<ticket channel=\"{ticket.channel}\">\n{_safe(ticket.text)}\n</ticket>\n\n"
            "Return the JSON object now.")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_response(content: str) -> dict:
    """Pull the JSON object out of the model's reply. Never raises."""
    match = re.search(r"\{.*\}", content or "", re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    answer = str(data.get("answer", "")).strip()
    citations = [str(c).strip() for c in data.get("citations", []) if str(c).strip()]
    can_answer = bool(data.get("can_answer")) and bool(answer)
    return {"can_answer": can_answer, "answer": answer, "citations": citations,
            "parse_ok": bool(data)}


def _offline_answer(passages) -> dict:
    """Extractive stand-in: copies the resolution steps of the best passage."""
    top = passages[0]
    steps = re.findall(r"^\d+\..*$", top.text, re.MULTILINE)
    body = "\n".join(steps[:4]) if steps else top.text.split("\n", 1)[-1][:500]
    return {"can_answer": True, "answer": body, "citations": [top.passage_id], "parse_ok": True}


class Generator:
    def __init__(self, settings):
        self.settings = settings
        self.client = LLMClient(settings) if settings.llm_provider != "offline" else None

    def draft(self, ticket, passages) -> dict:
        """Returns {"can_answer", "answer", "citations", "tokens", "error"}."""
        if self.client is None:
            return {**_offline_answer(passages), "tokens": 0, "error": ""}
        try:
            result = self.client.complete(build_messages(ticket, passages))
        except ProviderError as exc:
            return {"can_answer": False, "answer": "", "citations": [], "tokens": 0,
                    "parse_ok": False, "error": str(exc)}
        parsed = parse_response(result["content"])
        return {**parsed, "tokens": result["tokens"], "error": "" if parsed["parse_ok"]
                else "model reply was not valid JSON"}


def with_disclosure(answer: str, citations: list) -> str:
    """Added by code, not the model, so it is always there (Ravi: tell me it's automated)."""
    sources = ", ".join(sorted({c.split("#")[0] for c in citations}))
    return (f"{answer}\n\n---\nThis reply was drafted automatically from CloudServe documentation "
            f"({sources}). If it does not solve your problem, reply and a support agent will follow up.")
