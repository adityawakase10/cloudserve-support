# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""A small HTTP API in front of the same pipeline the harness uses.

    uvicorn src.api:app --port 8000
    then open http://localhost:8000/docs to try it in the browser.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import SupportPipeline

app = FastAPI(title="CloudServe support assistant")
_pipeline = None


def get_pipeline() -> SupportPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = SupportPipeline(datetime.now(timezone.utc).strftime("api-%Y%m%d"))
    return _pipeline


class TicketIn(BaseModel):
    ticket_id: str
    channel: str
    subject: Optional[str] = ""
    body: str
    received_at: Optional[str] = ""
    customer_id: Optional[str] = ""
    customer_name: Optional[str] = ""
    customer_tier: Optional[str] = "standard"
    customer_region: Optional[str] = ""
    language_fluency: Optional[str] = ""


@app.get("/health")
def health():
    p = get_pipeline()
    return {"status": "ok", "auto_respond_enabled": not p.kill_switch_on()}


@app.post("/tickets")
def submit_ticket(ticket: TicketIn):
    _, outcome = get_pipeline().process(ticket.model_dump())
    return {"ticket_id": outcome.ticket_id, "action": outcome.action, "reason": outcome.reason,
            "answer": outcome.answer if outcome.action == "auto_respond" else "",
            "citations": outcome.citations, "escalation_summary": outcome.escalation_summary,
            "guardrails": outcome.guardrails}
